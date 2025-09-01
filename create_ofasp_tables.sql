-- OpenASP Catalog Database Schema
-- Based on catalog.json structure analysis

-- 볼륨 테이블 (DISK01, DISK02, TEST, TEST_VOLUME)
CREATE TABLE IF NOT EXISTS aspuser.volumes (
    volume_id SERIAL PRIMARY KEY,
    volume_name VARCHAR(32) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 라이브러리 테이블 (TESTLIB, PRODLIB, XMLLIB, JAVA, COB, CL, SMED, LAYOUT, etc.)
CREATE TABLE IF NOT EXISTS aspuser.libraries (
    library_id SERIAL PRIMARY KEY,
    library_name VARCHAR(32) NOT NULL,
    volume_id INTEGER REFERENCES aspuser.volumes(volume_id) ON DELETE CASCADE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(volume_id, library_name)
);

-- 오브젝트 테이블 (프로그램, 데이터셋, 맵 등 모든 오브젝트)
CREATE TABLE IF NOT EXISTS aspuser.objects (
    object_id SERIAL PRIMARY KEY,
    object_name VARCHAR(128) NOT NULL,
    library_id INTEGER REFERENCES aspuser.libraries(library_id) ON DELETE CASCADE,
    object_type VARCHAR(32) NOT NULL CHECK (object_type IN ('PGM', 'DATASET', 'MAP', 'COPYBOOK', 'JOB', 'LAYOUT')),
    description TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    version VARCHAR(16),
    UNIQUE(library_id, object_name)
);

-- 프로그램 상세 정보
CREATE TABLE IF NOT EXISTS aspuser.programs (
    program_id SERIAL PRIMARY KEY,
    object_id INTEGER REFERENCES aspuser.objects(object_id) ON DELETE CASCADE,
    pgm_type VARCHAR(32) CHECK (pgm_type IN ('JAVA', 'COBOL', 'CL', 'SHELL')),
    pgm_name VARCHAR(128),
    class_file VARCHAR(256),
    source_file VARCHAR(256),
    jar_file VARCHAR(256),
    shell_file VARCHAR(256),
    executable VARCHAR(256),
    main_method BOOLEAN DEFAULT FALSE,
    asp_ready BOOLEAN DEFAULT FALSE,
    japanese_support BOOLEAN DEFAULT FALSE,
    naming_convention VARCHAR(32),
    execution_mode VARCHAR(32),
    dependencies TEXT,
    original_source VARCHAR(256),
    encoding VARCHAR(32) DEFAULT 'UTF-8',
    UNIQUE(object_id)
);

-- 데이터셋 상세 정보
CREATE TABLE IF NOT EXISTS aspuser.datasets (
    dataset_id SERIAL PRIMARY KEY,
    object_id INTEGER REFERENCES aspuser.objects(object_id) ON DELETE CASCADE,
    rec_type VARCHAR(8) CHECK (rec_type IN ('FB', 'VB')),
    rec_len INTEGER,
    encoding VARCHAR(32) DEFAULT 'utf-8',
    records_count INTEGER,
    output_format VARCHAR(32),
    japanese_encoding VARCHAR(32),
    original_file VARCHAR(256),
    layout_used VARCHAR(128),
    converted_at TIMESTAMP,
    UNIQUE(object_id)
);

-- 데이터셋 변환 정보
CREATE TABLE IF NOT EXISTS aspuser.dataset_conversions (
    conversion_id SERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES aspuser.datasets(dataset_id) ON DELETE CASCADE,
    source_encoding VARCHAR(32),
    target_encoding VARCHAR(32),
    source_file VARCHAR(512),
    layout_file VARCHAR(512),
    schema_file VARCHAR(512),
    converted_records INTEGER,
    conversion_date TIMESTAMP,
    record_length INTEGER,
    so_code INTEGER,
    si_code INTEGER,
    sosi_handling VARCHAR(16),
    japanese_encoding VARCHAR(32),
    UNIQUE(dataset_id)
);

-- 맵 상세 정보
CREATE TABLE IF NOT EXISTS aspuser.maps (
    map_id SERIAL PRIMARY KEY,
    object_id INTEGER REFERENCES aspuser.objects(object_id) ON DELETE CASCADE,
    map_type VARCHAR(32) CHECK (map_type IN ('SMED', 'HTML')),
    map_file VARCHAR(128),
    rows INTEGER DEFAULT 24,
    cols INTEGER DEFAULT 80,
    responsive BOOLEAN DEFAULT FALSE,
    UNIQUE(object_id)
);

-- 카피북 상세 정보
CREATE TABLE IF NOT EXISTS aspuser.copybooks (
    copybook_id SERIAL PRIMARY KEY,
    object_id INTEGER REFERENCES aspuser.objects(object_id) ON DELETE CASCADE,
    copybook_type VARCHAR(32) CHECK (copybook_type IN ('COBOL')),
    source_file VARCHAR(256),
    encoding VARCHAR(32) DEFAULT 'shift_jis',
    UNIQUE(object_id)
);

-- 작업 상세 정보
CREATE TABLE IF NOT EXISTS aspuser.jobs (
    job_id SERIAL PRIMARY KEY,
    object_id INTEGER REFERENCES aspuser.objects(object_id) ON DELETE CASCADE,
    job_type VARCHAR(32) CHECK (job_type IN ('BATCH')),
    schedule VARCHAR(32),
    command VARCHAR(512),
    UNIQUE(object_id)
);

-- 레이아웃 상세 정보
CREATE TABLE IF NOT EXISTS aspuser.layouts (
    layout_id SERIAL PRIMARY KEY,
    object_id INTEGER REFERENCES aspuser.objects(object_id) ON DELETE CASCADE,
    rec_fm VARCHAR(8) CHECK (rec_fm IN ('FB', 'VB')),
    lrecl VARCHAR(16),
    UNIQUE(object_id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_libraries_volume ON aspuser.libraries(volume_id);
CREATE INDEX IF NOT EXISTS idx_objects_library ON aspuser.objects(library_id);
CREATE INDEX IF NOT EXISTS idx_objects_type ON aspuser.objects(object_type);
CREATE INDEX IF NOT EXISTS idx_programs_object ON aspuser.programs(object_id);
CREATE INDEX IF NOT EXISTS idx_datasets_object ON aspuser.datasets(object_id);
CREATE INDEX IF NOT EXISTS idx_maps_object ON aspuser.maps(object_id);
CREATE INDEX IF NOT EXISTS idx_copybooks_object ON aspuser.copybooks(object_id);
CREATE INDEX IF NOT EXISTS idx_jobs_object ON aspuser.jobs(object_id);
CREATE INDEX IF NOT EXISTS idx_layouts_object ON aspuser.layouts(object_id);

-- 트리거 함수: updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION aspuser.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성
CREATE TRIGGER update_volumes_updated_at BEFORE UPDATE ON aspuser.volumes 
    FOR EACH ROW EXECUTE FUNCTION aspuser.update_updated_at_column();
    
CREATE TRIGGER update_libraries_updated_at BEFORE UPDATE ON aspuser.libraries 
    FOR EACH ROW EXECUTE FUNCTION aspuser.update_updated_at_column();
    
CREATE TRIGGER update_objects_updated_at BEFORE UPDATE ON aspuser.objects 
    FOR EACH ROW EXECUTE FUNCTION aspuser.update_updated_at_column();

-- 권한 설정
GRANT ALL ON SCHEMA aspuser TO aspuser;
GRANT ALL ON ALL TABLES IN SCHEMA aspuser TO aspuser;
GRANT ALL ON ALL SEQUENCES IN SCHEMA aspuser TO aspuser;