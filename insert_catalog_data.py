#!/usr/bin/env python3
"""
OpenASP Catalog Data Import Script
catalog.json의 데이터를 PostgreSQL ofasp 데이터베이스에 INSERT
"""

import json
import psycopg2
from datetime import datetime
import sys

def connect_to_db():
    """PostgreSQL 데이터베이스 연결"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="ofasp",
            user="aspuser",
            password="aspuser123"
        )
        return conn
    except Exception as e:
        print(f"데이터베이스 연결 실패: {e}")
        sys.exit(1)

def load_catalog_json():
    """catalog.json 파일 로드"""
    try:
        with open('/home/aspuser/app/config/catalog.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"catalog.json 로드 실패: {e}")
        sys.exit(1)

def parse_timestamp(ts_str):
    """타임스탬프 문자열을 PostgreSQL TIMESTAMP로 변환"""
    if not ts_str:
        return None
    try:
        # ISO 형식 처리
        if ts_str.endswith('Z'):
            return datetime.fromisoformat(ts_str[:-1])
        else:
            return datetime.fromisoformat(ts_str)
    except:
        return None

def insert_volume(cur, volume_name):
    """볼륨 INSERT"""
    cur.execute("""
        INSERT INTO aspuser.volumes (volume_name, description) 
        VALUES (%s, %s) 
        ON CONFLICT (volume_name) DO NOTHING
        RETURNING volume_id
    """, (volume_name, f"OpenASP Volume: {volume_name}"))
    
    result = cur.fetchone()
    if result:
        return result[0]
    else:
        # 이미 존재하는 경우 ID 조회
        cur.execute("SELECT volume_id FROM aspuser.volumes WHERE volume_name = %s", (volume_name,))
        return cur.fetchone()[0]

def insert_library(cur, library_name, volume_id):
    """라이브러리 INSERT"""
    cur.execute("""
        INSERT INTO aspuser.libraries (library_name, volume_id, description) 
        VALUES (%s, %s, %s) 
        ON CONFLICT (volume_id, library_name) DO NOTHING
        RETURNING library_id
    """, (library_name, volume_id, f"OpenASP Library: {library_name}"))
    
    result = cur.fetchone()
    if result:
        return result[0]
    else:
        # 이미 존재하는 경우 ID 조회
        cur.execute("SELECT library_id FROM aspuser.libraries WHERE volume_id = %s AND library_name = %s", 
                   (volume_id, library_name))
        return cur.fetchone()[0]

def insert_object(cur, object_name, library_id, obj_data):
    """오브젝트 INSERT"""
    object_type = obj_data.get('TYPE', 'DATASET')
    description = obj_data.get('DESCRIPTION', '')
    version = obj_data.get('VERSION', '1.0')
    created_at = parse_timestamp(obj_data.get('CREATED'))
    updated_at = parse_timestamp(obj_data.get('UPDATED'))
    
    cur.execute("""
        INSERT INTO aspuser.objects (object_name, library_id, object_type, description, version, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (library_id, object_name) DO UPDATE SET
            object_type = EXCLUDED.object_type,
            description = EXCLUDED.description,
            version = EXCLUDED.version,
            updated_at = EXCLUDED.updated_at
        RETURNING object_id
    """, (object_name, library_id, object_type, description, version, created_at, updated_at))
    
    return cur.fetchone()[0]

def insert_program_details(cur, object_id, obj_data):
    """프로그램 상세 정보 INSERT"""
    if obj_data.get('TYPE') != 'PGM':
        return
        
    cur.execute("""
        INSERT INTO aspuser.programs (
            object_id, pgm_type, pgm_name, class_file, source_file, jar_file, 
            shell_file, executable, main_method, asp_ready, japanese_support,
            naming_convention, execution_mode, dependencies, original_source, encoding
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (object_id) DO UPDATE SET
            pgm_type = EXCLUDED.pgm_type,
            pgm_name = EXCLUDED.pgm_name,
            class_file = EXCLUDED.class_file,
            source_file = EXCLUDED.source_file,
            jar_file = EXCLUDED.jar_file,
            shell_file = EXCLUDED.shell_file,
            executable = EXCLUDED.executable,
            main_method = EXCLUDED.main_method,
            asp_ready = EXCLUDED.asp_ready,
            japanese_support = EXCLUDED.japanese_support,
            naming_convention = EXCLUDED.naming_convention,
            execution_mode = EXCLUDED.execution_mode,
            dependencies = EXCLUDED.dependencies,
            original_source = EXCLUDED.original_source,
            encoding = EXCLUDED.encoding
    """, (
        object_id,
        obj_data.get('PGMTYPE'),
        obj_data.get('PGMNAME'),
        obj_data.get('CLASSFILE'),
        obj_data.get('SOURCEFILE'),
        obj_data.get('JARFILE'),
        obj_data.get('SHELLFILE'),
        obj_data.get('EXECUTABLE'),
        obj_data.get('MAIN_METHOD', False),
        obj_data.get('ASP_READY', False),
        obj_data.get('JAPANESE_SUPPORT', False),
        obj_data.get('NAMING_CONVENTION'),
        obj_data.get('EXECUTION_MODE'),
        obj_data.get('DEPENDENCIES'),
        obj_data.get('ORIGINAL_SOURCE'),
        obj_data.get('ENCODING', 'UTF-8')
    ))

def insert_dataset_details(cur, object_id, obj_data):
    """데이터셋 상세 정보 INSERT"""
    if obj_data.get('TYPE') != 'DATASET':
        return
        
    cur.execute("""
        INSERT INTO aspuser.datasets (
            object_id, rec_type, rec_len, encoding, records_count, 
            output_format, japanese_encoding, original_file, layout_used, converted_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (object_id) DO UPDATE SET
            rec_type = EXCLUDED.rec_type,
            rec_len = EXCLUDED.rec_len,
            encoding = EXCLUDED.encoding,
            records_count = EXCLUDED.records_count,
            output_format = EXCLUDED.output_format,
            japanese_encoding = EXCLUDED.japanese_encoding,
            original_file = EXCLUDED.original_file,
            layout_used = EXCLUDED.layout_used,
            converted_at = EXCLUDED.converted_at
    """, (
        object_id,
        obj_data.get('RECTYPE') or obj_data.get('RECFM'),
        obj_data.get('RECLEN') or obj_data.get('LRECL'),
        obj_data.get('ENCODING'),
        obj_data.get('RECORDS_COUNT'),
        obj_data.get('OUTPUT_FORMAT'),
        obj_data.get('JAPANESE_ENCODING'),
        obj_data.get('ORIGINAL_FILE'),
        obj_data.get('LAYOUT_USED'),
        parse_timestamp(obj_data.get('CONVERTED_AT'))
    ))
    
    # 변환 정보가 있으면 INSERT
    conversion = obj_data.get('CONVERSION')
    if conversion:
        insert_dataset_conversion(cur, object_id, conversion)

def insert_dataset_conversion(cur, dataset_id, conversion_data):
    """데이터셋 변환 정보 INSERT"""
    # 먼저 dataset_id를 가져옴 (datasets 테이블에서)
    cur.execute("SELECT dataset_id FROM aspuser.datasets WHERE object_id = %s", (dataset_id,))
    result = cur.fetchone()
    if not result:
        return
    
    actual_dataset_id = result[0]
    
    cur.execute("""
        INSERT INTO aspuser.dataset_conversions (
            dataset_id, source_encoding, target_encoding, source_file, layout_file, 
            schema_file, converted_records, conversion_date, record_length,
            so_code, si_code, sosi_handling, japanese_encoding
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (dataset_id) DO UPDATE SET
            source_encoding = EXCLUDED.source_encoding,
            target_encoding = EXCLUDED.target_encoding,
            source_file = EXCLUDED.source_file,
            layout_file = EXCLUDED.layout_file,
            schema_file = EXCLUDED.schema_file,
            converted_records = EXCLUDED.converted_records,
            conversion_date = EXCLUDED.conversion_date,
            record_length = EXCLUDED.record_length,
            so_code = EXCLUDED.so_code,
            si_code = EXCLUDED.si_code,
            sosi_handling = EXCLUDED.sosi_handling,
            japanese_encoding = EXCLUDED.japanese_encoding
    """, (
        actual_dataset_id,
        conversion_data.get('source_encoding') or conversion_data.get('SOURCE_ENCODING'),
        conversion_data.get('target_encoding'),
        conversion_data.get('SOURCE_FILE'),
        conversion_data.get('LAYOUT_FILE'),
        conversion_data.get('SCHEMA_FILE'),
        conversion_data.get('CONVERTED_RECORDS') or conversion_data.get('converted_records'),
        parse_timestamp(conversion_data.get('CONVERSION_DATE') or conversion_data.get('conversion_date')),
        conversion_data.get('record_length'),
        conversion_data.get('SOSI_CONFIG', {}).get('so_code'),
        conversion_data.get('SOSI_CONFIG', {}).get('si_code'),
        conversion_data.get('SOSI_CONFIG', {}).get('sosi_handling'),
        conversion_data.get('SOSI_CONFIG', {}).get('japanese_encoding')
    ))

def insert_map_details(cur, object_id, obj_data):
    """맵 상세 정보 INSERT"""
    if obj_data.get('TYPE') != 'MAP':
        return
        
    cur.execute("""
        INSERT INTO aspuser.maps (object_id, map_type, map_file, rows, cols, responsive)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (object_id) DO UPDATE SET
            map_type = EXCLUDED.map_type,
            map_file = EXCLUDED.map_file,
            rows = EXCLUDED.rows,
            cols = EXCLUDED.cols,
            responsive = EXCLUDED.responsive
    """, (
        object_id,
        obj_data.get('MAPTYPE'),
        obj_data.get('MAPFILE'),
        obj_data.get('ROWS', 24),
        obj_data.get('COLS', 80),
        obj_data.get('RESPONSIVE', False)
    ))

def insert_copybook_details(cur, object_id, obj_data):
    """카피북 상세 정보 INSERT"""
    if obj_data.get('TYPE') != 'COPYBOOK':
        return
        
    cur.execute("""
        INSERT INTO aspuser.copybooks (object_id, copybook_type, source_file, encoding)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (object_id) DO UPDATE SET
            copybook_type = EXCLUDED.copybook_type,
            source_file = EXCLUDED.source_file,
            encoding = EXCLUDED.encoding
    """, (
        object_id,
        obj_data.get('COPYBOOKTYPE'),
        obj_data.get('SOURCEFILE'),
        obj_data.get('ENCODING', 'shift_jis')
    ))

def insert_job_details(cur, object_id, obj_data):
    """작업 상세 정보 INSERT"""
    if obj_data.get('TYPE') != 'JOB':
        return
        
    cur.execute("""
        INSERT INTO aspuser.jobs (object_id, job_type, schedule, command)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (object_id) DO UPDATE SET
            job_type = EXCLUDED.job_type,
            schedule = EXCLUDED.schedule,
            command = EXCLUDED.command
    """, (
        object_id,
        obj_data.get('JOBTYPE'),
        obj_data.get('SCHEDULE'),
        obj_data.get('COMMAND')
    ))

def insert_layout_details(cur, object_id, obj_data):
    """레이아웃 상세 정보 INSERT"""
    if obj_data.get('TYPE') != 'LAYOUT':
        return
        
    cur.execute("""
        INSERT INTO aspuser.layouts (object_id, rec_fm, lrecl)
        VALUES (%s, %s, %s)
        ON CONFLICT (object_id) DO UPDATE SET
            rec_fm = EXCLUDED.rec_fm,
            lrecl = EXCLUDED.lrecl
    """, (
        object_id,
        obj_data.get('RECFM'),
        obj_data.get('LRECL')
    ))

def main():
    """메인 함수"""
    print("OpenASP Catalog 데이터 가져오기 시작...")
    
    conn = connect_to_db()
    cur = conn.cursor()
    
    catalog_data = load_catalog_json()
    
    try:
        # 각 볼륨에 대해 처리
        for volume_name, volume_data in catalog_data.items():
            if not isinstance(volume_data, dict):
                continue
                
            print(f"볼륨 처리중: {volume_name}")
            volume_id = insert_volume(cur, volume_name)
            
            # 각 라이브러리에 대해 처리
            for library_name, library_data in volume_data.items():
                if not isinstance(library_data, dict):
                    continue
                    
                print(f"  라이브러리 처리중: {library_name}")
                library_id = insert_library(cur, library_name, volume_id)
                
                # 각 오브젝트에 대해 처리
                for object_name, obj_data in library_data.items():
                    if not isinstance(obj_data, dict):
                        continue
                        
                    print(f"    오브젝트 처리중: {object_name}")
                    object_id = insert_object(cur, object_name, library_id, obj_data)
                    
                    # 타입별 상세 정보 INSERT
                    obj_type = obj_data.get('TYPE', 'DATASET')
                    if obj_type == 'PGM':
                        insert_program_details(cur, object_id, obj_data)
                    elif obj_type == 'DATASET':
                        insert_dataset_details(cur, object_id, obj_data)
                    elif obj_type == 'MAP':
                        insert_map_details(cur, object_id, obj_data)
                    elif obj_type == 'COPYBOOK':
                        insert_copybook_details(cur, object_id, obj_data)
                    elif obj_type == 'JOB':
                        insert_job_details(cur, object_id, obj_data)
                    elif obj_type == 'LAYOUT':
                        insert_layout_details(cur, object_id, obj_data)
        
        conn.commit()
        print("데이터 가져오기 완료!")
        
        # 통계 출력
        cur.execute("SELECT COUNT(*) FROM aspuser.volumes")
        volume_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM aspuser.libraries")
        library_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM aspuser.objects")
        object_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM aspuser.programs")
        program_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM aspuser.datasets")
        dataset_count = cur.fetchone()[0]
        
        print(f"\n=== 가져오기 통계 ===")
        print(f"볼륨: {volume_count}개")
        print(f"라이브러리: {library_count}개")
        print(f"전체 오브젝트: {object_count}개")
        print(f"프로그램: {program_count}개")
        print(f"데이터셋: {dataset_count}개")
        
    except Exception as e:
        conn.rollback()
        print(f"오류 발생: {e}")
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()