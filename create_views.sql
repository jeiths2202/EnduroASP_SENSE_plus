-- OpenASP 데이터베이스 뷰 생성 스크립트
-- 각 상세 테이블에 대해 오브젝트 정보가 포함된 뷰를 생성

-- 1. 데이터셋 뷰
CREATE OR REPLACE VIEW aspuser.v_datasets AS
SELECT 
    d.dataset_id,
    v.volume_name,
    l.library_name,
    o.object_name,
    o.object_path,
    d.rec_type,
    d.rec_len,
    d.encoding,
    o.file_size,
    d.created_at,
    d.updated_at
FROM aspuser.datasets d
JOIN aspuser.objects o ON d.object_id = o.object_id
JOIN aspuser.libraries l ON o.library_id = l.library_id
JOIN aspuser.volumes v ON o.volume_id = v.volume_id
ORDER BY v.volume_name, l.library_name, o.object_name;

COMMENT ON VIEW aspuser.v_datasets IS '데이터셋 상세 정보 뷰 (볼륨/라이브러리/오브젝트명 포함)';

-- 2. 프로그램 뷰
CREATE OR REPLACE VIEW aspuser.v_programs AS
SELECT 
    p.program_id,
    v.volume_name,
    l.library_name,
    o.object_name,
    o.object_path,
    p.pgm_type,
    p.encoding,
    p.compile_date,
    o.file_size,
    p.created_at,
    p.updated_at
FROM aspuser.programs p
JOIN aspuser.objects o ON p.object_id = o.object_id
JOIN aspuser.libraries l ON o.library_id = l.library_id
JOIN aspuser.volumes v ON o.volume_id = v.volume_id
ORDER BY v.volume_name, l.library_name, o.object_name;

COMMENT ON VIEW aspuser.v_programs IS '프로그램 상세 정보 뷰 (볼륨/라이브러리/오브젝트명 포함)';

-- 3. 맵 뷰
CREATE OR REPLACE VIEW aspuser.v_maps AS
SELECT 
    m.map_id,
    v.volume_name,
    l.library_name,
    o.object_name,
    o.object_path,
    m.map_type,
    m.width,
    m.height,
    o.file_size,
    m.created_at,
    m.updated_at
FROM aspuser.maps m
JOIN aspuser.objects o ON m.object_id = o.object_id
JOIN aspuser.libraries l ON o.library_id = l.library_id
JOIN aspuser.volumes v ON o.volume_id = v.volume_id
ORDER BY v.volume_name, l.library_name, o.object_name;

COMMENT ON VIEW aspuser.v_maps IS '맵 상세 정보 뷰 (볼륨/라이브러리/오브젝트명 포함)';

-- 4. 카피북 뷰
CREATE OR REPLACE VIEW aspuser.v_copybooks AS
SELECT 
    c.copybook_id,
    v.volume_name,
    l.library_name,
    o.object_name,
    o.object_path,
    c.copybook_type,
    c.encoding,
    o.file_size,
    c.created_at,
    c.updated_at
FROM aspuser.copybooks c
JOIN aspuser.objects o ON c.object_id = o.object_id
JOIN aspuser.libraries l ON o.library_id = l.library_id
JOIN aspuser.volumes v ON o.volume_id = v.volume_id
ORDER BY v.volume_name, l.library_name, o.object_name;

COMMENT ON VIEW aspuser.v_copybooks IS '카피북 상세 정보 뷰 (볼륨/라이브러리/오브젝트명 포함)';

-- 5. 작업(JOB) 뷰
CREATE OR REPLACE VIEW aspuser.v_jobs AS
SELECT 
    j.job_id,
    v.volume_name,
    l.library_name,
    o.object_name,
    o.object_path,
    j.job_type,
    j.schedule_info,
    o.file_size,
    j.created_at,
    j.updated_at
FROM aspuser.jobs j
JOIN aspuser.objects o ON j.object_id = o.object_id
JOIN aspuser.libraries l ON o.library_id = l.library_id
JOIN aspuser.volumes v ON o.volume_id = v.volume_id
ORDER BY v.volume_name, l.library_name, o.object_name;

COMMENT ON VIEW aspuser.v_jobs IS '작업 상세 정보 뷰 (볼륨/라이브러리/오브젝트명 포함)';

-- 6. 레이아웃 뷰
CREATE OR REPLACE VIEW aspuser.v_layouts AS
SELECT 
    lay.layout_id,
    v.volume_name,
    l.library_name,
    o.object_name,
    o.object_path,
    lay.layout_type,
    lay.layout_data,
    o.file_size,
    lay.created_at,
    lay.updated_at
FROM aspuser.layouts lay
JOIN aspuser.objects o ON lay.object_id = o.object_id
JOIN aspuser.libraries l ON o.library_id = l.library_id
JOIN aspuser.volumes v ON o.volume_id = v.volume_id
ORDER BY v.volume_name, l.library_name, o.object_name;

COMMENT ON VIEW aspuser.v_layouts IS '레이아웃 상세 정보 뷰 (볼륨/라이브러리/오브젝트명 포함)';

-- 7. 데이터셋 변환 이력 뷰
CREATE OR REPLACE VIEW aspuser.v_dataset_conversions AS
SELECT 
    dc.conversion_id,
    v.volume_name,
    l.library_name,
    o.object_name,
    d.rec_type,
    d.rec_len,
    dc.source_encoding,
    dc.target_encoding,
    dc.conversion_date
FROM aspuser.dataset_conversions dc
JOIN aspuser.datasets d ON dc.dataset_id = d.dataset_id
JOIN aspuser.objects o ON d.object_id = o.object_id
JOIN aspuser.libraries l ON o.library_id = l.library_id
JOIN aspuser.volumes v ON o.volume_id = v.volume_id
ORDER BY dc.conversion_date DESC;

COMMENT ON VIEW aspuser.v_dataset_conversions IS '데이터셋 변환 이력 뷰 (볼륨/라이브러리/오브젝트명 포함)';

-- 8. 전체 오브젝트 통합 뷰
CREATE OR REPLACE VIEW aspuser.v_all_objects AS
SELECT 
    v.volume_name,
    l.library_name,
    o.object_name,
    o.object_type,
    o.object_path,
    o.file_size,
    CASE 
        WHEN o.object_type = 'PGM' THEN p.pgm_type
        WHEN o.object_type = 'DATASET' THEN d.rec_type
        WHEN o.object_type = 'MAP' THEN m.map_type
        WHEN o.object_type = 'COPYBOOK' THEN c.copybook_type
        WHEN o.object_type = 'JOB' THEN j.job_type
        WHEN o.object_type = 'LAYOUT' THEN lay.layout_type
        ELSE NULL
    END as sub_type,
    CASE 
        WHEN o.object_type = 'DATASET' THEN d.rec_len::text
        WHEN o.object_type = 'MAP' THEN m.width || 'x' || m.height
        ELSE NULL
    END as dimensions,
    COALESCE(p.encoding, d.encoding, c.encoding, 'N/A') as encoding,
    o.created_at,
    o.updated_at
FROM aspuser.objects o
JOIN aspuser.libraries l ON o.library_id = l.library_id
JOIN aspuser.volumes v ON o.volume_id = v.volume_id
LEFT JOIN aspuser.programs p ON o.object_id = p.object_id
LEFT JOIN aspuser.datasets d ON o.object_id = d.object_id
LEFT JOIN aspuser.maps m ON o.object_id = m.object_id
LEFT JOIN aspuser.copybooks c ON o.object_id = c.object_id
LEFT JOIN aspuser.jobs j ON o.object_id = j.object_id
LEFT JOIN aspuser.layouts lay ON o.object_id = lay.object_id
ORDER BY v.volume_name, l.library_name, o.object_name;

COMMENT ON VIEW aspuser.v_all_objects IS '전체 오브젝트 통합 뷰 (모든 타입의 상세 정보 포함)';