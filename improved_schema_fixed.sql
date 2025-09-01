-- OpenASP AX 개선된 데이터베이스 스키마 (수정본)
-- 계층 구조: VOLUME -> LIBRARY -> OBJECT 
-- 각 레벨에서 적절한 UNIQUE 제약조건 적용

-- 1. 볼륨 테이블
CREATE TABLE aspuser.volumes (
    volume_id SERIAL PRIMARY KEY,
    volume_name VARCHAR(50) NOT NULL UNIQUE,
    volume_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 라이브러리 테이블 (개선: volume_id와 library_name 조합으로 UNIQUE)
CREATE TABLE aspuser.libraries (
    library_id SERIAL PRIMARY KEY,
    volume_id INTEGER NOT NULL,
    library_name VARCHAR(50) NOT NULL,
    library_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래키 제약조건
    CONSTRAINT fk_libraries_volume 
        FOREIGN KEY (volume_id) REFERENCES aspuser.volumes(volume_id) ON DELETE CASCADE,
    
    -- UNIQUE 제약조건: 같은 볼륨 내에서 라이브러리 이름은 중복될 수 없음
    CONSTRAINT uk_volume_library 
        UNIQUE (volume_id, library_name)
);

-- 3. 오브젝트 테이블 (개선: volume_id 추가, 전체 경로에서 유니크)
CREATE TABLE aspuser.objects (
    object_id SERIAL PRIMARY KEY,
    volume_id INTEGER NOT NULL,
    library_id INTEGER NOT NULL,
    object_name VARCHAR(100) NOT NULL,
    object_type VARCHAR(20) NOT NULL,
    object_path TEXT NOT NULL,
    file_size BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래키 제약조건
    CONSTRAINT fk_objects_volume 
        FOREIGN KEY (volume_id) REFERENCES aspuser.volumes(volume_id) ON DELETE CASCADE,
    CONSTRAINT fk_objects_library 
        FOREIGN KEY (library_id) REFERENCES aspuser.libraries(library_id) ON DELETE CASCADE,
    
    -- UNIQUE 제약조건: 같은 볼륨/라이브러리 조합 내에서 오브젝트 이름은 중복될 수 없음
    CONSTRAINT uk_volume_library_object 
        UNIQUE (volume_id, library_id, object_name)
);

-- 4. 프로그램 테이블
CREATE TABLE aspuser.programs (
    program_id SERIAL PRIMARY KEY,
    object_id INTEGER NOT NULL,
    pgm_type VARCHAR(20) NOT NULL,
    encoding VARCHAR(20) DEFAULT 'UTF-8',
    compile_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_programs_object 
        FOREIGN KEY (object_id) REFERENCES aspuser.objects(object_id) ON DELETE CASCADE
);

-- 5. 데이터셋 테이블
CREATE TABLE aspuser.datasets (
    dataset_id SERIAL PRIMARY KEY,
    object_id INTEGER NOT NULL,
    rec_type VARCHAR(10) NOT NULL,
    rec_len INTEGER,
    encoding VARCHAR(20) DEFAULT 'UTF-8',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_datasets_object 
        FOREIGN KEY (object_id) REFERENCES aspuser.objects(object_id) ON DELETE CASCADE
);

-- 6. 데이터셋 변환 테이블
CREATE TABLE aspuser.dataset_conversions (
    conversion_id SERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL,
    source_encoding VARCHAR(20) NOT NULL,
    target_encoding VARCHAR(20) NOT NULL,
    conversion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_conversions_dataset 
        FOREIGN KEY (dataset_id) REFERENCES aspuser.datasets(dataset_id) ON DELETE CASCADE
);

-- 7. 맵 테이블
CREATE TABLE aspuser.maps (
    map_id SERIAL PRIMARY KEY,
    object_id INTEGER NOT NULL,
    map_type VARCHAR(20) NOT NULL,
    width INTEGER,
    height INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_maps_object 
        FOREIGN KEY (object_id) REFERENCES aspuser.objects(object_id) ON DELETE CASCADE
);

-- 8. 카피북 테이블
CREATE TABLE aspuser.copybooks (
    copybook_id SERIAL PRIMARY KEY,
    object_id INTEGER NOT NULL,
    copybook_type VARCHAR(20) NOT NULL,
    encoding VARCHAR(20) DEFAULT 'UTF-8',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_copybooks_object 
        FOREIGN KEY (object_id) REFERENCES aspuser.objects(object_id) ON DELETE CASCADE
);

-- 9. 작업 테이블
CREATE TABLE aspuser.jobs (
    job_id SERIAL PRIMARY KEY,
    object_id INTEGER NOT NULL,
    job_type VARCHAR(20) NOT NULL,
    schedule_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_jobs_object 
        FOREIGN KEY (object_id) REFERENCES aspuser.objects(object_id) ON DELETE CASCADE
);

-- 10. 레이아웃 테이블
CREATE TABLE aspuser.layouts (
    layout_id SERIAL PRIMARY KEY,
    object_id INTEGER NOT NULL,
    layout_type VARCHAR(20) NOT NULL,
    layout_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_layouts_object 
        FOREIGN KEY (object_id) REFERENCES aspuser.objects(object_id) ON DELETE CASCADE
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX idx_libraries_volume_id ON aspuser.libraries(volume_id);
CREATE INDEX idx_libraries_volume_library ON aspuser.libraries(volume_id, library_name);
CREATE INDEX idx_objects_volume_id ON aspuser.objects(volume_id);
CREATE INDEX idx_objects_library_id ON aspuser.objects(library_id);
CREATE INDEX idx_objects_volume_library_id ON aspuser.objects(volume_id, library_id);
CREATE INDEX idx_objects_volume_library_name ON aspuser.objects(volume_id, library_id, object_name);
CREATE INDEX idx_objects_type ON aspuser.objects(object_type);

-- 주석 추가
COMMENT ON TABLE aspuser.volumes IS 'OpenASP 볼륨 정보 (DISK01, DISK02 등)';
COMMENT ON TABLE aspuser.libraries IS '라이브러리 정보 (TESTLIB, PRODLIB 등) - 볼륨별로 중복 가능';
COMMENT ON TABLE aspuser.objects IS '오브젝트 정보 (프로그램, 데이터셋 등) - 볼륨/라이브러리 조합별로 중복 가능';

COMMENT ON CONSTRAINT uk_volume_library ON aspuser.libraries IS '볼륨 내에서 라이브러리명 중복 방지';
COMMENT ON CONSTRAINT uk_volume_library_object ON aspuser.objects IS '볼륨/라이브러리 조합 내에서 오브젝트명 중복 방지';