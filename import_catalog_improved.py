#!/usr/bin/env python3
"""
OpenASP AX 카탈로그 데이터 가져오기 스크립트 (개선된 스키마용)
catalog.json 파일을 파싱하여 개선된 PostgreSQL 스키마로 데이터를 가져옵니다.
"""

import json
import psycopg2
from psycopg2 import sql
import os
import sys
from datetime import datetime

# 데이터베이스 연결 설정
DB_CONFIG = {
    'host': 'localhost',
    'database': 'ofasp',
    'user': 'aspuser',
    'password': 'aspuser123',
    'port': 5432
}

def connect_db():
    """데이터베이스 연결"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        sys.exit(1)

def load_catalog():
    """catalog.json 파일 로드"""
    catalog_path = '/home/aspuser/app/config/catalog.json'
    try:
        with open(catalog_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Catalog load error: {e}")
        sys.exit(1)

def import_volumes(conn, catalog):
    """볼륨 데이터 가져오기"""
    cursor = conn.cursor()
    
    # 기존 데이터 삭제
    cursor.execute("TRUNCATE aspuser.volumes CASCADE")
    
    volumes_data = []
    for volume_name, volume_data in catalog.items():
        volume_path = volume_data.get('path', f'/volume/{volume_name}')
        volumes_data.append((volume_name, volume_path))
    
    # 볼륨 데이터 삽입
    cursor.executemany("""
        INSERT INTO aspuser.volumes (volume_name, volume_path) 
        VALUES (%s, %s)
    """, volumes_data)
    
    print(f"✓ {len(volumes_data)}개 볼륨 가져오기 완료")
    return cursor.rowcount

def import_libraries(conn, catalog):
    """라이브러리 데이터 가져오기"""
    cursor = conn.cursor()
    
    # 볼륨 ID 매핑 생성
    cursor.execute("SELECT volume_id, volume_name FROM aspuser.volumes")
    volume_mapping = {name: id for id, name in cursor.fetchall()}
    
    libraries_data = []
    for volume_name, volume_data in catalog.items():
        volume_id = volume_mapping[volume_name]
        
        # 카탈로그 구조: VOLUME -> LIBRARY -> OBJECT
        for library_name, library_objects in volume_data.items():
            if isinstance(library_objects, dict):  # 라이브러리는 딕셔너리 형태
                library_path = f'/volume/{volume_name}/{library_name}'
                libraries_data.append((volume_id, library_name, library_path))
    
    # 라이브러리 데이터 삽입
    cursor.executemany("""
        INSERT INTO aspuser.libraries (volume_id, library_name, library_path) 
        VALUES (%s, %s, %s)
    """, libraries_data)
    
    print(f"✓ {len(libraries_data)}개 라이브러리 가져오기 완료")
    return cursor.rowcount

def import_objects(conn, catalog):
    """오브젝트 데이터 가져오기"""
    cursor = conn.cursor()
    
    # 볼륨 및 라이브러리 ID 매핑 생성
    cursor.execute("""
        SELECT l.library_id, l.volume_id, v.volume_name, l.library_name 
        FROM aspuser.libraries l 
        JOIN aspuser.volumes v ON l.volume_id = v.volume_id
    """)
    library_mapping = {}
    for library_id, volume_id, volume_name, library_name in cursor.fetchall():
        library_mapping[(volume_name, library_name)] = {
            'library_id': library_id,
            'volume_id': volume_id
        }
    
    objects_data = []
    programs_data = []
    datasets_data = []
    maps_data = []
    copybooks_data = []
    jobs_data = []
    layouts_data = []
    
    object_id_counter = 1
    
    for volume_name, volume_data in catalog.items():
        # 카탈로그 구조: VOLUME -> LIBRARY -> OBJECT
        for library_name, library_objects in volume_data.items():
            if isinstance(library_objects, dict):  # 라이브러리는 딕셔너리 형태
                lib_info = library_mapping.get((volume_name, library_name))
                if not lib_info:
                    print(f"Warning: Library mapping not found for {volume_name}/{library_name}")
                    continue
                    
                volume_id = lib_info['volume_id']
                library_id = lib_info['library_id']
                
                # 라이브러리 내의 모든 오브젝트 처리
                for object_name, object_data in library_objects.items():
                    if isinstance(object_data, dict):  # 오브젝트는 딕셔너리 형태
                        object_type = object_data.get('TYPE', 'UNKNOWN')
                        file_size = object_data.get('SIZE', 0)
                        object_path = f"/volume/{volume_name}/{library_name}/{object_name}"
                        
                        # 기본 오브젝트 정보
                        objects_data.append((
                            object_id_counter, volume_id, library_id, object_name, 
                            object_type, object_path, file_size
                        ))
                        
                        # 타입별 상세 정보
                        if object_type == 'PGM':
                            pgm_type = object_data.get('PGMTYPE', 'UNKNOWN')
                            encoding = object_data.get('ENCODING', 'UTF-8')
                            programs_data.append((object_id_counter, pgm_type, encoding))
                            
                        elif object_type == 'DATASET':
                            rec_type = object_data.get('RECTYPE', 'FB')
                            rec_len = object_data.get('RECLEN', 80)
                            encoding = object_data.get('ENCODING', 'UTF-8')
                            datasets_data.append((object_id_counter, rec_type, rec_len, encoding))
                            
                        elif object_type == 'MAP':
                            map_type = object_data.get('MAPTYPE', 'SMED')
                            width = object_data.get('WIDTH', 0)
                            height = object_data.get('HEIGHT', 0)
                            maps_data.append((object_id_counter, map_type, width, height))
                            
                        elif object_type == 'COPYBOOK':
                            copybook_type = object_data.get('COPYBOOKTYPE', 'COBOL')
                            encoding = object_data.get('ENCODING', 'UTF-8')
                            copybooks_data.append((object_id_counter, copybook_type, encoding))
                            
                        elif object_type == 'JOB':
                            job_type = object_data.get('JOBTYPE', 'BATCH')
                            schedule_info = object_data.get('SCHEDULEINFO', '')
                            jobs_data.append((object_id_counter, job_type, schedule_info))
                            
                        elif object_type == 'LAYOUT':
                            layout_type = object_data.get('LAYOUTTYPE', 'SCREEN')
                            layout_data_str = json.dumps(object_data.get('LAYOUTDATA', {}))
                            layouts_data.append((object_id_counter, layout_type, layout_data_str))
                        
                        object_id_counter += 1
    
    # 오브젝트 데이터 삽입 (명시적 ID 포함)
    cursor.executemany("""
        INSERT INTO aspuser.objects (object_id, volume_id, library_id, object_name, object_type, object_path, file_size) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, objects_data)
    
    # 시퀀스 값 업데이트
    cursor.execute(f"SELECT setval('aspuser.objects_object_id_seq', {object_id_counter})")
    
    print(f"✓ {len(objects_data)}개 오브젝트 가져오기 완료")
    
    # 상세 테이블 데이터 삽입
    if programs_data:
        cursor.executemany("""
            INSERT INTO aspuser.programs (object_id, pgm_type, encoding) 
            VALUES (%s, %s, %s)
        """, programs_data)
        print(f"  - {len(programs_data)}개 프로그램")
    
    if datasets_data:
        cursor.executemany("""
            INSERT INTO aspuser.datasets (object_id, rec_type, rec_len, encoding) 
            VALUES (%s, %s, %s, %s)
        """, datasets_data)
        print(f"  - {len(datasets_data)}개 데이터셋")
    
    if maps_data:
        cursor.executemany("""
            INSERT INTO aspuser.maps (object_id, map_type, width, height) 
            VALUES (%s, %s, %s, %s)
        """, maps_data)
        print(f"  - {len(maps_data)}개 맵")
    
    if copybooks_data:
        cursor.executemany("""
            INSERT INTO aspuser.copybooks (object_id, copybook_type, encoding) 
            VALUES (%s, %s, %s)
        """, copybooks_data)
        print(f"  - {len(copybooks_data)}개 카피북")
    
    if jobs_data:
        cursor.executemany("""
            INSERT INTO aspuser.jobs (object_id, job_type, schedule_info) 
            VALUES (%s, %s, %s)
        """, jobs_data)
        print(f"  - {len(jobs_data)}개 작업")
    
    if layouts_data:
        cursor.executemany("""
            INSERT INTO aspuser.layouts (object_id, layout_type, layout_data) 
            VALUES (%s, %s, %s)
        """, layouts_data)
        print(f"  - {len(layouts_data)}개 레이아웃")
    
    return len(objects_data)

def verify_import(conn):
    """데이터 가져오기 검증"""
    cursor = conn.cursor()
    
    print("\n=== 데이터 가져오기 검증 ===")
    
    # 각 테이블 레코드 수 확인
    tables = ['volumes', 'libraries', 'objects', 'programs', 'datasets', 'maps', 'copybooks', 'jobs', 'layouts']
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM aspuser.{table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count}건")
    
    # 계층 구조 확인
    print("\n=== 계층 구조 확인 ===")
    cursor.execute("""
        SELECT v.volume_name, COUNT(DISTINCT l.library_id) as libraries, 
               COUNT(o.object_id) as objects
        FROM aspuser.volumes v
        LEFT JOIN aspuser.libraries l ON v.volume_id = l.volume_id
        LEFT JOIN aspuser.objects o ON l.library_id = o.library_id
        GROUP BY v.volume_id, v.volume_name
        ORDER BY v.volume_name
    """)
    
    for volume_name, lib_count, obj_count in cursor.fetchall():
        print(f"  {volume_name}: {lib_count}개 라이브러리, {obj_count}개 오브젝트")
    
    # UNIQUE 제약조건 테스트
    print("\n=== UNIQUE 제약조건 테스트 ===")
    
    # 같은 볼륨 내 라이브러리 중복 테스트
    try:
        cursor.execute("""
            SELECT volume_id, library_name, COUNT(*) 
            FROM aspuser.libraries 
            GROUP BY volume_id, library_name 
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"  ⚠️  볼륨 내 라이브러리 중복 발견: {len(duplicates)}건")
        else:
            print("  ✓ 볼륨 내 라이브러리 이름 유니크 확인")
    except Exception as e:
        print(f"  ❌ 라이브러리 중복 검사 실패: {e}")
    
    # 같은 볼륨/라이브러리 내 오브젝트 중복 테스트
    try:
        cursor.execute("""
            SELECT volume_id, library_id, object_name, COUNT(*) 
            FROM aspuser.objects 
            GROUP BY volume_id, library_id, object_name 
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"  ⚠️  볼륨/라이브러리 내 오브젝트 중복 발견: {len(duplicates)}건")
        else:
            print("  ✓ 볼륨/라이브러리 내 오브젝트 이름 유니크 확인")
    except Exception as e:
        print(f"  ❌ 오브젝트 중복 검사 실패: {e}")

def main():
    """메인 실행 함수"""
    print("OpenASP AX 카탈로그 데이터 가져오기 (개선된 스키마)")
    print("=" * 50)
    
    # 데이터베이스 연결
    conn = connect_db()
    conn.autocommit = False
    
    try:
        # 카탈로그 로드
        catalog = load_catalog()
        print(f"✓ catalog.json 로드 완료 ({len(catalog)}개 볼륨)")
        
        # 데이터 가져오기
        volume_count = import_volumes(conn, catalog)
        library_count = import_libraries(conn, catalog)
        object_count = import_objects(conn, catalog)
        
        # 트랜잭션 커밋
        conn.commit()
        print(f"\n✓ 모든 데이터 가져오기 완료!")
        print(f"  - 볼륨: {volume_count}개")
        print(f"  - 라이브러리: {library_count}개") 
        print(f"  - 오브젝트: {object_count}개")
        
        # 검증
        verify_import(conn)
        
    except Exception as e:
        print(f"\n❌ 데이터 가져오기 실패: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()