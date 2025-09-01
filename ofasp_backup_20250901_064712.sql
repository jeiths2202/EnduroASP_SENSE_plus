--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13 (Debian 15.13-0+deb12u1)
-- Dumped by pg_dump version 15.13 (Debian 15.13-0+deb12u1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: aspuser; Type: SCHEMA; Schema: -; Owner: aspuser
--

CREATE SCHEMA aspuser;


ALTER SCHEMA aspuser OWNER TO aspuser;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: aspuser; Owner: aspuser
--

CREATE FUNCTION aspuser.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION aspuser.update_updated_at_column() OWNER TO aspuser;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: copybooks; Type: TABLE; Schema: aspuser; Owner: aspuser
--

CREATE TABLE aspuser.copybooks (
    copybook_id integer NOT NULL,
    object_id integer,
    copybook_type character varying(32),
    source_file character varying(256),
    encoding character varying(32) DEFAULT 'shift_jis'::character varying,
    CONSTRAINT copybooks_copybook_type_check CHECK (((copybook_type)::text = 'COBOL'::text))
);


ALTER TABLE aspuser.copybooks OWNER TO aspuser;

--
-- Name: copybooks_copybook_id_seq; Type: SEQUENCE; Schema: aspuser; Owner: aspuser
--

CREATE SEQUENCE aspuser.copybooks_copybook_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE aspuser.copybooks_copybook_id_seq OWNER TO aspuser;

--
-- Name: copybooks_copybook_id_seq; Type: SEQUENCE OWNED BY; Schema: aspuser; Owner: aspuser
--

ALTER SEQUENCE aspuser.copybooks_copybook_id_seq OWNED BY aspuser.copybooks.copybook_id;


--
-- Name: dataset_conversions; Type: TABLE; Schema: aspuser; Owner: aspuser
--

CREATE TABLE aspuser.dataset_conversions (
    conversion_id integer NOT NULL,
    dataset_id integer,
    source_encoding character varying(32),
    target_encoding character varying(32),
    source_file character varying(512),
    layout_file character varying(512),
    schema_file character varying(512),
    converted_records integer,
    conversion_date timestamp without time zone,
    record_length integer,
    so_code integer,
    si_code integer,
    sosi_handling character varying(16),
    japanese_encoding character varying(32)
);


ALTER TABLE aspuser.dataset_conversions OWNER TO aspuser;

--
-- Name: dataset_conversions_conversion_id_seq; Type: SEQUENCE; Schema: aspuser; Owner: aspuser
--

CREATE SEQUENCE aspuser.dataset_conversions_conversion_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE aspuser.dataset_conversions_conversion_id_seq OWNER TO aspuser;

--
-- Name: dataset_conversions_conversion_id_seq; Type: SEQUENCE OWNED BY; Schema: aspuser; Owner: aspuser
--

ALTER SEQUENCE aspuser.dataset_conversions_conversion_id_seq OWNED BY aspuser.dataset_conversions.conversion_id;


--
-- Name: datasets; Type: TABLE; Schema: aspuser; Owner: aspuser
--

CREATE TABLE aspuser.datasets (
    dataset_id integer NOT NULL,
    object_id integer,
    rec_type character varying(8),
    rec_len integer,
    encoding character varying(32) DEFAULT 'utf-8'::character varying,
    records_count integer,
    output_format character varying(32),
    japanese_encoding character varying(32),
    original_file character varying(256),
    layout_used character varying(128),
    converted_at timestamp without time zone,
    CONSTRAINT datasets_rec_type_check CHECK (((rec_type)::text = ANY ((ARRAY['FB'::character varying, 'VB'::character varying])::text[])))
);


ALTER TABLE aspuser.datasets OWNER TO aspuser;

--
-- Name: datasets_dataset_id_seq; Type: SEQUENCE; Schema: aspuser; Owner: aspuser
--

CREATE SEQUENCE aspuser.datasets_dataset_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE aspuser.datasets_dataset_id_seq OWNER TO aspuser;

--
-- Name: datasets_dataset_id_seq; Type: SEQUENCE OWNED BY; Schema: aspuser; Owner: aspuser
--

ALTER SEQUENCE aspuser.datasets_dataset_id_seq OWNED BY aspuser.datasets.dataset_id;


--
-- Name: jobs; Type: TABLE; Schema: aspuser; Owner: aspuser
--

CREATE TABLE aspuser.jobs (
    job_id integer NOT NULL,
    object_id integer,
    job_type character varying(32),
    schedule character varying(32),
    command character varying(512),
    CONSTRAINT jobs_job_type_check CHECK (((job_type)::text = 'BATCH'::text))
);


ALTER TABLE aspuser.jobs OWNER TO aspuser;

--
-- Name: jobs_job_id_seq; Type: SEQUENCE; Schema: aspuser; Owner: aspuser
--

CREATE SEQUENCE aspuser.jobs_job_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE aspuser.jobs_job_id_seq OWNER TO aspuser;

--
-- Name: jobs_job_id_seq; Type: SEQUENCE OWNED BY; Schema: aspuser; Owner: aspuser
--

ALTER SEQUENCE aspuser.jobs_job_id_seq OWNED BY aspuser.jobs.job_id;


--
-- Name: layouts; Type: TABLE; Schema: aspuser; Owner: aspuser
--

CREATE TABLE aspuser.layouts (
    layout_id integer NOT NULL,
    object_id integer,
    rec_fm character varying(8),
    lrecl character varying(16),
    CONSTRAINT layouts_rec_fm_check CHECK (((rec_fm)::text = ANY ((ARRAY['FB'::character varying, 'VB'::character varying])::text[])))
);


ALTER TABLE aspuser.layouts OWNER TO aspuser;

--
-- Name: layouts_layout_id_seq; Type: SEQUENCE; Schema: aspuser; Owner: aspuser
--

CREATE SEQUENCE aspuser.layouts_layout_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE aspuser.layouts_layout_id_seq OWNER TO aspuser;

--
-- Name: layouts_layout_id_seq; Type: SEQUENCE OWNED BY; Schema: aspuser; Owner: aspuser
--

ALTER SEQUENCE aspuser.layouts_layout_id_seq OWNED BY aspuser.layouts.layout_id;


--
-- Name: libraries; Type: TABLE; Schema: aspuser; Owner: aspuser
--

CREATE TABLE aspuser.libraries (
    library_id integer NOT NULL,
    library_name character varying(32) NOT NULL,
    volume_id integer,
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE aspuser.libraries OWNER TO aspuser;

--
-- Name: libraries_library_id_seq; Type: SEQUENCE; Schema: aspuser; Owner: aspuser
--

CREATE SEQUENCE aspuser.libraries_library_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE aspuser.libraries_library_id_seq OWNER TO aspuser;

--
-- Name: libraries_library_id_seq; Type: SEQUENCE OWNED BY; Schema: aspuser; Owner: aspuser
--

ALTER SEQUENCE aspuser.libraries_library_id_seq OWNED BY aspuser.libraries.library_id;


--
-- Name: maps; Type: TABLE; Schema: aspuser; Owner: aspuser
--

CREATE TABLE aspuser.maps (
    map_id integer NOT NULL,
    object_id integer,
    map_type character varying(32),
    map_file character varying(128),
    rows integer DEFAULT 24,
    cols integer DEFAULT 80,
    responsive boolean DEFAULT false,
    CONSTRAINT maps_map_type_check CHECK (((map_type)::text = ANY ((ARRAY['SMED'::character varying, 'HTML'::character varying])::text[])))
);


ALTER TABLE aspuser.maps OWNER TO aspuser;

--
-- Name: maps_map_id_seq; Type: SEQUENCE; Schema: aspuser; Owner: aspuser
--

CREATE SEQUENCE aspuser.maps_map_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE aspuser.maps_map_id_seq OWNER TO aspuser;

--
-- Name: maps_map_id_seq; Type: SEQUENCE OWNED BY; Schema: aspuser; Owner: aspuser
--

ALTER SEQUENCE aspuser.maps_map_id_seq OWNED BY aspuser.maps.map_id;


--
-- Name: objects; Type: TABLE; Schema: aspuser; Owner: aspuser
--

CREATE TABLE aspuser.objects (
    object_id integer NOT NULL,
    object_name character varying(128) NOT NULL,
    library_id integer,
    object_type character varying(32) NOT NULL,
    description text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    version character varying(16),
    CONSTRAINT objects_object_type_check CHECK (((object_type)::text = ANY ((ARRAY['PGM'::character varying, 'DATASET'::character varying, 'MAP'::character varying, 'COPYBOOK'::character varying, 'JOB'::character varying, 'LAYOUT'::character varying])::text[])))
);


ALTER TABLE aspuser.objects OWNER TO aspuser;

--
-- Name: objects_object_id_seq; Type: SEQUENCE; Schema: aspuser; Owner: aspuser
--

CREATE SEQUENCE aspuser.objects_object_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE aspuser.objects_object_id_seq OWNER TO aspuser;

--
-- Name: objects_object_id_seq; Type: SEQUENCE OWNED BY; Schema: aspuser; Owner: aspuser
--

ALTER SEQUENCE aspuser.objects_object_id_seq OWNED BY aspuser.objects.object_id;


--
-- Name: programs; Type: TABLE; Schema: aspuser; Owner: aspuser
--

CREATE TABLE aspuser.programs (
    program_id integer NOT NULL,
    object_id integer,
    pgm_type character varying(32),
    pgm_name character varying(128),
    class_file character varying(256),
    source_file character varying(256),
    jar_file character varying(256),
    shell_file character varying(256),
    executable character varying(256),
    main_method boolean DEFAULT false,
    asp_ready boolean DEFAULT false,
    japanese_support boolean DEFAULT false,
    naming_convention character varying(32),
    execution_mode character varying(32),
    dependencies text,
    original_source character varying(256),
    encoding character varying(32) DEFAULT 'UTF-8'::character varying,
    CONSTRAINT programs_pgm_type_check CHECK (((pgm_type)::text = ANY ((ARRAY['JAVA'::character varying, 'COBOL'::character varying, 'CL'::character varying, 'SHELL'::character varying])::text[])))
);


ALTER TABLE aspuser.programs OWNER TO aspuser;

--
-- Name: programs_program_id_seq; Type: SEQUENCE; Schema: aspuser; Owner: aspuser
--

CREATE SEQUENCE aspuser.programs_program_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE aspuser.programs_program_id_seq OWNER TO aspuser;

--
-- Name: programs_program_id_seq; Type: SEQUENCE OWNED BY; Schema: aspuser; Owner: aspuser
--

ALTER SEQUENCE aspuser.programs_program_id_seq OWNED BY aspuser.programs.program_id;


--
-- Name: volumes; Type: TABLE; Schema: aspuser; Owner: aspuser
--

CREATE TABLE aspuser.volumes (
    volume_id integer NOT NULL,
    volume_name character varying(32) NOT NULL,
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE aspuser.volumes OWNER TO aspuser;

--
-- Name: volumes_volume_id_seq; Type: SEQUENCE; Schema: aspuser; Owner: aspuser
--

CREATE SEQUENCE aspuser.volumes_volume_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE aspuser.volumes_volume_id_seq OWNER TO aspuser;

--
-- Name: volumes_volume_id_seq; Type: SEQUENCE OWNED BY; Schema: aspuser; Owner: aspuser
--

ALTER SEQUENCE aspuser.volumes_volume_id_seq OWNED BY aspuser.volumes.volume_id;


--
-- Name: copybooks copybook_id; Type: DEFAULT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.copybooks ALTER COLUMN copybook_id SET DEFAULT nextval('aspuser.copybooks_copybook_id_seq'::regclass);


--
-- Name: dataset_conversions conversion_id; Type: DEFAULT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.dataset_conversions ALTER COLUMN conversion_id SET DEFAULT nextval('aspuser.dataset_conversions_conversion_id_seq'::regclass);


--
-- Name: datasets dataset_id; Type: DEFAULT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.datasets ALTER COLUMN dataset_id SET DEFAULT nextval('aspuser.datasets_dataset_id_seq'::regclass);


--
-- Name: jobs job_id; Type: DEFAULT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.jobs ALTER COLUMN job_id SET DEFAULT nextval('aspuser.jobs_job_id_seq'::regclass);


--
-- Name: layouts layout_id; Type: DEFAULT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.layouts ALTER COLUMN layout_id SET DEFAULT nextval('aspuser.layouts_layout_id_seq'::regclass);


--
-- Name: libraries library_id; Type: DEFAULT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.libraries ALTER COLUMN library_id SET DEFAULT nextval('aspuser.libraries_library_id_seq'::regclass);


--
-- Name: maps map_id; Type: DEFAULT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.maps ALTER COLUMN map_id SET DEFAULT nextval('aspuser.maps_map_id_seq'::regclass);


--
-- Name: objects object_id; Type: DEFAULT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.objects ALTER COLUMN object_id SET DEFAULT nextval('aspuser.objects_object_id_seq'::regclass);


--
-- Name: programs program_id; Type: DEFAULT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.programs ALTER COLUMN program_id SET DEFAULT nextval('aspuser.programs_program_id_seq'::regclass);


--
-- Name: volumes volume_id; Type: DEFAULT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.volumes ALTER COLUMN volume_id SET DEFAULT nextval('aspuser.volumes_volume_id_seq'::regclass);


--
-- Data for Name: copybooks; Type: TABLE DATA; Schema: aspuser; Owner: aspuser
--

COPY aspuser.copybooks (copybook_id, object_id, copybook_type, source_file, encoding) FROM stdin;
1	101	COBOL	MITDSP	shift_jis
2	102	COBOL	EMPLECPY	shift_jis
\.


--
-- Data for Name: dataset_conversions; Type: TABLE DATA; Schema: aspuser; Owner: aspuser
--

COPY aspuser.dataset_conversions (conversion_id, dataset_id, source_encoding, target_encoding, source_file, layout_file, schema_file, converted_records, conversion_date, record_length, so_code, si_code, sosi_handling, japanese_encoding) FROM stdin;
1	8	JAK	\N	/data/assets/ebcdic/DEMO.SAM.ebc	/home/aspuser/app/volume/DISK01/LAYOUT/SAM001.LAYOUT	\N	29	2025-08-05 04:57:49.559114	11	\N	\N	\N	\N
2	9	JAK	\N	/data/assets/ebcdic/DEMO.SAM.ebc	/home/aspuser/app/volume/DISK01/LAYOUT/SAM001.LAYOUT	\N	1	2025-08-05 00:57:22.751802	\N	\N	\N	\N	\N
3	10	JAK	\N	/data/assets/ebcdic/DEMO.SAM.ebc	/home/aspuser/app/volume/DISK01/LAYOUT/SAM001.LAYOUT	\N	1	2025-08-05 00:57:48.583728	\N	\N	\N	\N	\N
4	11	JAK	\N	/data/assets/ebcdic/DEMO.SAM.ebc	/home/aspuser/app/volume/DISK01/LAYOUT/SAM001.LAYOUT	\N	1	2025-08-05 00:58:00.722295	\N	\N	\N	\N	\N
5	12	JAK	\N	/data/assets/ebcdic/DEMO.SAM.ebc	/home/aspuser/app/volume/DISK01/LAYOUT/SAM001.LAYOUT	\N	80	2025-08-05 05:06:29.944797	4	\N	\N	\N	\N
6	13	JAK	\N	/data/assets/ebcdic/DEMO.SAM.ebc	/home/aspuser/app/volume/DISK01/LAYOUT/SAM001.LAYOUT	\N	80	2025-08-05 05:11:40.68161	4	\N	\N	\N	\N
7	14	JAK	\N	/data/assets/ebcdic/DEMO.SAM.ebc	/home/aspuser/app/volume/DISK01/LAYOUT/SAM001.LAYOUT	\N	80	2025-08-05 07:37:03.477404	4	\N	\N	\N	\N
8	15	JAK	\N	/data/assets/ebcdic/DEMO.SAM.ebc	/home/aspuser/app/volume/DISK01/LAYOUT/SAM001.LAYOUT	\N	4	2025-08-05 07:39:49.51482	80	\N	\N	\N	\N
9	16	JAK	\N	/data/assets/ebcdic/DEMO.SAM.ebc	/home/aspuser/app/volume/DISK01/LAYOUT/SAM001.LAYOUT	\N	4	2025-08-05 07:56:30.240297	80	\N	\N	\N	\N
10	17	JAK	\N	/data/assets/ebcdic/DEMO.SAM.ebc	/home/aspuser/app/volume/DISK01/LAYOUT/SAM001.LAYOUT	\N	4	2025-08-05 07:56:40.662309	80	\N	\N	\N	\N
11	18	JAK	\N	/data/assets/ebcdic/DEMO.SAM.ebc	/home/aspuser/app/volume/DISK01/LAYOUT/SAM001.LAYOUT	\N	4	2025-08-05 07:56:46.662845	80	\N	\N	\N	\N
12	19	JAK	\N	/data/assets/ebcdic/DEMO.SAM.ebc	volume/DISK01/LAYOUT/SAM001.LAYOUT	\N	4	2025-08-05 07:59:24.965472	80	\N	\N	\N	\N
13	26	JAK	shift_jis	/data/assets/ebcdic/DEMO.SAM.ebc	/tmp/sam001_schema.json	/tmp/sam001_schema.json	4	2025-08-05 08:07:33.269705	80	40	41	SPACE	sjis
\.


--
-- Data for Name: datasets; Type: TABLE DATA; Schema: aspuser; Owner: aspuser
--

COPY aspuser.datasets (dataset_id, object_id, rec_type, rec_len, encoding, records_count, output_format, japanese_encoding, original_file, layout_used, converted_at) FROM stdin;
1	2	FB	80	shift_jis	\N	\N	\N	\N	\N	\N
2	3	FB	80	shift_jis	\N	\N	\N	\N	\N	\N
3	4	VB	256	utf-8	\N	\N	\N	\N	\N	\N
4	20	FB	128	utf-8	\N	\N	\N	\N	\N	\N
5	52	FB	80	utf-8	\N	\N	\N	\N	\N	\N
6	56	FB	80	shift_jis	\N	\N	\N	\N	\N	\N
7	57	FB	80	shift_jis	\N	\N	\N	\N	\N	\N
8	58	FB	11	ascii	\N	\N	\N	\N	\N	\N
9	59	FB	80	ascii	\N	\N	\N	\N	\N	\N
10	60	FB	80	ascii	\N	\N	\N	\N	\N	\N
11	61	FB	80	ascii	\N	\N	\N	\N	\N	\N
12	62	FB	4	ascii	\N	\N	\N	\N	\N	\N
13	63	FB	4	ascii	\N	\N	\N	\N	\N	\N
14	64	FB	4	ascii	\N	\N	\N	\N	\N	\N
15	65	FB	80	ascii	\N	\N	\N	\N	\N	\N
16	66	FB	80	ascii	\N	\N	\N	\N	\N	\N
17	67	FB	80	ascii	\N	\N	\N	\N	\N	\N
18	68	FB	80	ascii	\N	\N	\N	\N	\N	\N
19	69	FB	80	ascii	\N	\N	\N	\N	\N	\N
20	70	FB	80	JAK	1	flat	utf-8	DEMO.SAM.ebc	SAM001	2025-08-05 13:42:33.819
21	73	FB	80	shift_jis	1	flat	\N	DEMO.SAM.ebc	SAM001	2025-08-28 08:43:45.234
22	91	FB	80	utf-8	\N	\N	\N	\N	\N	\N
23	92	FB	120	utf-8	\N	\N	\N	\N	\N	\N
24	94	FB	100	utf-8	\N	\N	\N	\N	\N	\N
25	95	VB	256	utf-8	\N	\N	\N	\N	\N	\N
26	122	FB	80	shift_jis	\N	\N	\N	\N	\N	\N
\.


--
-- Data for Name: jobs; Type: TABLE DATA; Schema: aspuser; Owner: aspuser
--

COPY aspuser.jobs (job_id, object_id, job_type, schedule, command) FROM stdin;
1	121	BATCH	DAILY	backup_daily.sh
\.


--
-- Data for Name: layouts; Type: TABLE DATA; Schema: aspuser; Owner: aspuser
--

COPY aspuser.layouts (layout_id, object_id, rec_fm, lrecl) FROM stdin;
1	120	FB	80
\.


--
-- Data for Name: libraries; Type: TABLE DATA; Schema: aspuser; Owner: aspuser
--

COPY aspuser.libraries (library_id, library_name, volume_id, description, created_at, updated_at) FROM stdin;
2	TESTLIB	2	OpenASP Library: TESTLIB	2025-09-01 05:24:24.383895	2025-09-01 05:24:24.383895
3	PRODLIB	2	OpenASP Library: PRODLIB	2025-09-01 05:24:24.383895	2025-09-01 05:24:24.383895
4	XMLLIB	2	OpenASP Library: XMLLIB	2025-09-01 05:24:24.383895	2025-09-01 05:24:24.383895
5	JAVA	2	OpenASP Library: JAVA	2025-09-01 05:24:24.383895	2025-09-01 05:24:24.383895
6	COB	2	OpenASP Library: COB	2025-09-01 05:24:24.383895	2025-09-01 05:24:24.383895
7	CL	2	OpenASP Library: CL	2025-09-01 05:24:24.383895	2025-09-01 05:24:24.383895
8	SMED	2	OpenASP Library: SMED	2025-09-01 05:24:24.383895	2025-09-01 05:24:24.383895
9	LAYOUT	2	OpenASP Library: LAYOUT	2025-09-01 05:24:24.383895	2025-09-01 05:24:24.383895
10	BACKUPLIB	3	OpenASP Library: BACKUPLIB	2025-09-01 05:24:24.383895	2025-09-01 05:24:24.383895
11	PRODLIB	3	OpenASP Library: PRODLIB	2025-09-01 05:24:24.383895	2025-09-01 05:24:24.383895
12	LIB1	4	OpenASP Library: LIB1	2025-09-01 05:24:24.383895	2025-09-01 05:24:24.383895
13	TEST_LIB	5	OpenASP Library: TEST_LIB	2025-09-01 05:24:24.383895	2025-09-01 05:24:24.383895
\.


--
-- Data for Name: maps; Type: TABLE DATA; Schema: aspuser; Owner: aspuser
--

COPY aspuser.maps (map_id, object_id, map_type, map_file, rows, cols, responsive) FROM stdin;
1	8	HTML	CUSTINQ.html	24	80	t
2	10	HTML	NEWMAP.html	30	120	t
3	106	SMED	MAINMENU	24	80	f
4	107	SMED	MAIN001	24	80	f
5	108	SMED	MENU	24	80	f
6	109	SMED	MENU001	24	80	f
7	110	SMED	MENU003	24	80	f
8	111	SMED	MENU004	24	80	f
9	112	SMED	MENU005	24	80	f
10	113	SMED	MENU006	24	80	f
11	114	SMED	MENU007	24	80	f
12	115	SMED	SUB001	24	80	f
13	116	SMED	MSGSAMP1	24	80	f
14	117	SMED	BROWSE_MENU	24	80	f
15	118	SMED	LOGO	24	80	f
16	119	SMED	ENDUROASP_LOGO	24	80	f
\.


--
-- Data for Name: objects; Type: TABLE DATA; Schema: aspuser; Owner: aspuser
--

COPY aspuser.objects (object_id, object_name, library_id, object_type, description, created_at, updated_at, version) FROM stdin;
2	EMPLOYEE.FB	2	DATASET	Employee master file	2025-07-21 10:00:00	2025-07-21 10:00:00	1.0
3	EMPLOYEE_SJIS.FB	2	DATASET	Employee master file (SJIS encoded)	2025-07-30 10:00:00	2025-07-30 10:00:00	1.0
4	PAYROLL.VB	2	DATASET	Payroll data file	2025-07-21 10:00:00	2025-07-21 10:00:00	1.0
5	LOGOPGM1	2	PGM	Main menu program	2025-07-21 10:00:00	2025-07-21 10:00:00	1.0
6	PRT001	2	PGM	Employee dataset reader - reads EMPLOYEE.FB via OVRF mapping and outputs to stdout	2025-08-16 06:55:00	2025-08-28 04:20:00	1.2
7	PAYROLL01	2	PGM	Monthly payroll calculation	2025-07-21 10:00:00	2025-07-21 10:00:00	2.1
8	CUSTINQ	2	MAP	Customer inquiry screen	2025-07-21 10:00:00	2025-07-21 10:00:00	1.0
9	NEWPROGRAM	2	PGM	Test program	2025-07-21 06:27:53.247399	2025-07-21 06:27:53.247399	1.5
10	NEWMAP	2	MAP	Test map screen	2025-07-21 06:28:07.885211	2025-07-21 06:28:07.885211	1.0
11	TestProgram	2	PGM	Sample ASP Java Program for CALL testing	2025-07-21 07:29:47.889315	2025-07-21 07:29:47.889315	1.0
12	EnhancedTestProgram	2	PGM	Enhanced ASP Java Program with Phase 2 features	2025-07-21 09:04:29.408589	2025-07-21 09:04:29.408589	1.0
13	test_shell	2	PGM	Test shell program	2025-07-21 09:46:17.516107	2025-07-21 09:46:17.516107	1.0
14	PGM000	2	PGM	Main control program	2025-07-22 14:05:15.2834	2025-07-22 14:05:15.283416	1.0
15	PGM004	2	PGM	Update search program	2025-07-22 14:05:15.303216	2025-07-22 14:05:15.303228	1.0
16	PGM002	2	PGM	Employee add program	2025-07-22 14:05:15.321355	2025-07-22 14:05:15.321386	1.0
17	PGM003	2	PGM	Employee add confirm program	2025-07-22 14:05:15.339143	2025-07-22 14:05:15.339154	1.0
18	PGM001	2	PGM	Employee inquiry program	2025-07-22 14:05:15.355814	2025-07-22 14:05:15.355825	1.0
19	CUINP001	2	PGM	Customer data input program for FB format SAM files	2025-07-24 17:04:00	2025-07-24 17:04:00	1.0
20	CUSTOMER.SAM001	2	DATASET	CUSTOMER.SAM001 dataset	2025-07-24 17:07:39.168118	2025-07-24 17:57:25.374656	1.0
21	test_job	2	PGM	Test job for SMBJOB/REFJOB demonstration	2025-07-25 10:00:00	2025-07-25 10:00:00	1.0
22	long_job	2	PGM	Long running job for demonstration	2025-07-25 10:01:00	2025-07-25 10:01:00	1.0
23	EMPINQ	2	PGM	Employee inquiry CL command processor	2025-07-25 14:00:00	2025-07-25 14:00:00	1.0
24	EMPADD	2	PGM	Employee add CL command processor	2025-07-25 14:00:00	2025-07-25 14:00:00	1.0
25	EMPUPD	2	PGM	Employee update CL command processor	2025-07-25 14:00:00	2025-07-25 14:00:00	1.0
26	EMPDEL	2	PGM	Employee delete CL command processor	2025-07-25 14:00:00	2025-07-25 14:00:00	1.0
27	BACKUP	2	PGM	Database backup CL procedure	2025-07-25 14:00:00	2025-07-25 14:00:00	1.0
28	RESTORE	2	PGM	Database restore CL procedure	2025-07-25 14:00:00	2025-07-25 14:00:00	1.0
29	SYSCLEAN	2	PGM	System cleanup CL procedure	2025-07-25 14:00:00	2025-07-25 14:00:00	1.0
30	LONGJOB	2	PGM	Long running job CL (3+ minutes) for resource monitoring test	2025-07-25 14:00:00	2025-07-25 14:00:00	1.0
31	REPORT	2	PGM	Report generation CL procedure	2025-07-25 14:00:00	2025-07-25 14:00:00	1.0
32	FILEUTIL	2	PGM	File utility CL commands (CRTFILE/DLTFILE operations)	2025-07-25 14:00:00	2025-07-25 14:00:00	1.0
33	EMPFILEJAVA	2	PGM	Employee file I/O processor for EMPLOYEE.FB dataset	2025-07-25 14:00:00	2025-07-25 14:00:00	1.0
34	TESTCL	2	PGM	Fujitsu ASP Test CL Program	2025-07-26 01:00:00	2025-07-26 01:00:00	1.0
35	TESTJP_ASP	2	PGM	日本語メッセージを含むFujitsu ASP CLテストプログラム	2025-07-26 01:00:00	2025-07-26 01:00:00	1.0
36	HelloASP	2	PGM	Hello ASP message display Java program	2025-07-27 15:42:00	2025-07-27 15:42:00	1.0
37	HELLOASP	2	PGM	Hello ASP message display Java program (uppercase alias)	2025-07-27 15:42:00	2025-07-27 15:42:00	1.0
38	TESTCL1	2	PGM	Test CL program that calls HelloASP Java program	2025-07-27 15:42:00	2025-07-27 15:42:00	1.0
39	FILEUTIL_ASP	2	PGM	Fujitsu ASP File Utility CL (no DSP commands)	2025-07-26 02:00:00	2025-07-26 02:00:00	1.0
40	DATAPROC_ASP	2	PGM	Fujitsu ASP Data Processing CL (no DSP commands)	2025-07-26 02:00:00	2025-07-26 02:00:00	1.0
41	DAILY_BATCH	2	PGM	日次バッチ処理 - Fujitsu ASP CL	2025-07-26 03:00:00	2025-07-26 03:00:00	1.0
42	SYSTEM_CHECK	2	PGM	システムチェック - Fujitsu ASP CL	2025-07-26 03:00:00	2025-07-26 03:00:00	1.0
43	DATA_INIT	2	PGM	データ初期化 - Fujitsu ASP CL	2025-07-26 03:00:00	2025-07-26 03:00:00	1.0
44	FILEWRITE_ASP	2	PGM	ファイル書き込みサンプル - Fujitsu ASP CL	2025-07-27 01:00:00	2025-07-27 01:00:00	1.0
45	EMPLOYEE_WRITE	2	PGM	社員データ書き込み - Fujitsu ASP CL	2025-07-27 01:00:00	2025-07-27 01:00:00	1.0
46	REPORT_WRITE	2	PGM	レポート出力 - Fujitsu ASP CL	2025-07-27 01:00:00	2025-07-27 01:00:00	1.0
47	LOG_WRITE	2	PGM	ログ書き込み - Fujitsu ASP CL	2025-07-27 01:00:00	2025-07-27 01:00:00	1.0
48	EMPREAD_CL	2	PGM	Employee file read CL - calls TESTPGM	2025-07-27 02:00:00	2025-07-27 02:00:00	1.0
49	TESTPGM	2	PGM	Employee data reader Java program	2025-07-27 02:00:00	2025-07-27 02:00:00	1.0
50	MSGSample	2	PGM	COBOL to Java converted program - Fujitsu ASP display file demonstration	2025-07-28 10:00:00	2025-07-28 10:00:00	1.0
51	MSGSAMPLE	2	PGM	COBOL to Java converted program - Fujitsu ASP display file demonstration (uppercase alias)	2025-07-28 10:00:00	2025-07-28 10:00:00	1.0
52	SAMDATA	2	DATASET	Sequential access method data file for MSGSample program	2025-07-28 10:00:00	2025-07-28 10:00:00	1.0
53	TESTMSG_CL	2	PGM	Test CL program for MSGSample execution	2025-07-28 10:00:00	2025-07-28 10:00:00	1.0
54	MSGSAMPLEBROWSERMENU	2	PGM	Enhanced SMED-based Japanese employee data browser using BROWSE_MENU map architecture	2025-07-28 18:00:00	2025-07-28 18:00:00	1.0
55	MSGSAMPLEBROWSERMENUJSON	2	PGM	Simplified JSON-based employee data browser - 5 employees only	2025-07-31 12:00:00	2025-07-31 12:00:00	1.0
56	EMPLOYEE_TEST.FB	2	DATASET	Test employee dataset for simplified browser - 5 records	2025-07-31 12:00:00	2025-07-31 12:00:00	1.0
57	EMP.INFO	2	DATASET	Employee Information File	2025-08-01 11:56:56.05548	2025-08-01 11:56:56.05548	1.0
58	DEMO.SAM.CONVERTED	2	DATASET	Converted from EBCDIC (JAK)	\N	2025-08-05 04:57:49.559133	1.0
59	DEMO.SAM.FIXED	2	DATASET	Converted from EBCDIC (JAK)	\N	2025-08-05 00:57:22.751788	1.0
60	DEMO.SAM.FINAL	2	DATASET	Converted from EBCDIC (JAK)	\N	2025-08-05 00:57:48.583713	1.0
61	DEMO.SAM.OUTPUT	2	DATASET	Converted from EBCDIC (JAK)	\N	2025-08-05 00:58:00.72228	1.0
62	/tmp/a.out	2	DATASET	Converted from EBCDIC (JAK)	\N	2025-08-05 05:06:29.944816	1.0
63	DEMO.SAM.FLAT	2	DATASET	Converted from EBCDIC (JAK)	\N	2025-08-05 05:11:40.681622	1.0
64	TEST.SAM.FB	2	DATASET	Converted from EBCDIC (JAK)	\N	2025-08-05 07:37:03.477488	1.0
65	TEST.SAM.FB80	2	DATASET	Converted from EBCDIC (JAK)	\N	2025-08-05 07:39:49.514835	1.0
66	DEMO.SAM.SOSI	2	DATASET	Converted from EBCDIC (JAK)	\N	2025-08-05 07:56:30.240316	1.0
67	DEMO.SAM.SOSI.FLAT	2	DATASET	Converted from EBCDIC (JAK)	\N	2025-08-05 07:56:40.662334	1.0
68	DEMO.SAM.REMOVE	2	DATASET	Converted from EBCDIC (JAK)	\N	2025-08-05 07:56:46.662856	1.0
69	DEMO.SOSI	2	DATASET	Converted from EBCDIC (JAK)	\N	2025-08-05 07:59:24.965496	1.0
70	SAM001.ASCII	2	DATASET	Dataset converted from DEMO.SAM.ebc via UI	\N	\N	1.0
71	CL001	2	PGM	CL001 - Basic CL command processor	2025-08-16 02:32:40	2025-08-16 02:32:40	1.0
72	CLTEST01	2	PGM	CLTEST01 - Test CL program for cmdRunner Phase 2 verification	2025-08-16 06:55:00	2025-08-16 06:55:00	1.0
73	SAM001	2	DATASET	Dataset converted from DEMO.SAM.ebc via UI	\N	\N	1.0
74	MAIN001	2	PGM	MAIN001 - Main Program (copied from JAVA library)	2025-08-25 10:31:22	2025-08-25 10:31:22	1.0
75	MAIN001Demo	2	PGM	MAIN001 Demo Program - Enhanced demonstration version	2025-08-25 10:31:22	2025-08-25 10:31:22	1.0
76	SimpleMAIN001Test	2	PGM	Simple test program for MAIN001 functionality	2025-08-25 10:31:22	2025-08-25 10:31:22	1.0
77	TSTJAVA1_TESTLIB	2	PGM	Test Java program (copied from JAVA library)	2025-08-25 10:31:22	2025-08-25 10:31:22	1.0
78	TestAbend	2	PGM	ABEND test program for system testing	2025-08-25 10:31:22	2025-08-25 10:31:22	1.0
79	JSONResponse	2	PGM	JSON response utility class	2025-08-25 10:31:22	2025-08-25 10:31:22	1.0
80	SUB001_TESTLIB	2	PGM	SUB001 Employee Information Display (copied from JAVA library)	2025-08-25 10:31:22	2025-08-25 10:31:22	1.0
81	MAIN001_TESTLIB	2	PGM	MAIN001 Main Program (copied from JAVA library)	2025-08-25 10:31:22	2025-08-25 10:31:22	1.0
82	DisplayOutputHandler	2	PGM	Display output handler utility	2025-08-25 10:31:22	2025-08-25 10:31:22	1.0
83	MAIN001Interactive	2	PGM	MAIN001 Interactive execution mode	2025-08-25 10:31:22	2025-08-25 10:31:22	1.0
84	MAIN001Test	2	PGM	MAIN001 Test program	2025-08-25 10:31:22	2025-08-25 10:31:22	1.0
85	CobolFileException	2	PGM	COBOL file exception handler	2025-08-25 10:31:22	2025-08-25 10:31:22	1.0
86	MitdspRecord	2	PGM	MITDSP record structure handler	2025-08-25 10:31:22	2025-08-25 10:31:22	1.0
87	OutputHandler	2	PGM	Output handler interface	2025-08-25 10:31:22	2025-08-25 10:31:22	1.0
88	DspFile	2	PGM	Display file handler	2025-08-25 10:31:22	2025-08-25 10:31:22	1.0
89	CobolDataConversionException	2	PGM	COBOL data conversion exception handler	2025-08-25 10:31:22	2025-08-25 10:31:22	1.0
90	WebUIService	2	PGM	Web UI service handler	2025-08-25 10:31:22	2025-08-25 10:31:22	1.0
91	TESTFILE	2	DATASET	TESTFILE dataset	2025-08-26 10:52:36.982258	2025-08-26 10:52:36.982258	1.0
92	CUSTOMER.FB	3	DATASET	Customer master file	2025-07-21 10:00:00	2025-07-21 10:00:00	1.0
93	BILLING	3	PGM	Monthly billing process	2025-07-21 10:00:00	2025-07-21 10:00:00	1.5
94	SALES.FB	3	DATASET	Sales data file with mixed English/Japanese content	2025-07-25 12:00:00	2025-07-25 12:00:00	1.0
95	REPORT.VB	3	DATASET	Report output file with variable length records	2025-07-25 12:00:00	2025-07-25 12:00:00	1.0
96	TESTCL	3	PGM	Fujitsu ASP Test CL Program	2025-07-26 01:00:00	2025-07-26 01:00:00	1.0
97	BACKUP_ASP	3	PGM	Fujitsu ASP Backup CL Program	2025-07-26 01:00:00	2025-07-26 01:00:00	1.0
98	REPORT_ASP	3	PGM	Fujitsu ASP Report Generation CL	2025-07-26 01:00:00	2025-07-26 01:00:00	1.0
99	CLEANUP_ASP	3	PGM	Fujitsu ASP System Cleanup CL	2025-07-26 01:00:00	2025-07-26 01:00:00	1.0
100	LONGRUN_ASP	3	PGM	Fujitsu ASP Long Running Job CL (3+ minutes)	2025-07-26 01:00:00	2025-07-26 01:00:00	1.0
101	MITDSP	4	COPYBOOK	Standard message definition copybook for Fujitsu ASP COBOLG SMED maps	2025-08-01 12:00:00	2025-08-01 12:00:00	1.0
102	EMPLECPY	4	COPYBOOK	Employee Record COPYBOOK - Fixed Block record structure for EMP.INFO dataset	2025-08-01 12:00:00	2025-08-01 12:00:00	1.0
103	MAIN001	5	PGM	MAIN001 for ASP system execution - 8-byte naming convention compliant	2025-08-01 16:30:00	2025-08-01 16:45:00	1.0
104	SUB001	5	PGM	SUB001 - Employee Information Display Program - 8-byte naming convention compliant	2025-08-01 16:30:00	2025-08-01 16:45:00	1.0
105	TSTJAVA1	5	PGM	TSTJAVA1 - Test Java program for cmdRunner Phase 2 verification (60 second sleep)	2025-08-16 06:55:00	2025-08-16 06:55:00	1.0
106	MAINMENU	8	MAP	SMED map: MAINMENU	2025-07-22 01:32:15.412519	2025-07-22 01:32:15.412533	1.0
107	MAIN001	8	MAP	SMED map: MAIN001 - Main menu map for Japanese management interface	2025-08-01 12:00:00	2025-08-01 12:00:00	1.0
108	MENU	8	MAP	SMED map: MENU - Base menu map	2025-08-02 12:00:00	2025-08-02 12:00:00	1.0
109	MENU001	8	MAP	SMED map: MENU001	2025-07-22 08:42:29.87144	2025-07-22 08:42:29.871449	1.0
110	MENU003	8	MAP	SMED map: MENU003	2025-07-22 08:42:29.888664	2025-07-22 08:42:29.888673	1.0
111	MENU004	8	MAP	SMED map: MENU004	2025-07-22 08:42:29.902722	2025-07-22 08:42:29.902732	1.0
112	MENU005	8	MAP	SMED map: MENU005	2025-07-22 08:42:29.917399	2025-07-22 08:42:29.91741	1.0
113	MENU006	8	MAP	SMED map: MENU006	2025-07-22 08:42:29.929681	2025-07-22 08:42:29.929691	1.0
114	MENU007	8	MAP	SMED map: MENU007	2025-07-22 08:42:29.942843	2025-07-22 08:42:29.942853	1.0
115	SUB001	8	MAP	SMED map: SUB001 - Employee information display map	2025-08-01 12:00:00	2025-08-01 12:00:00	1.0
116	MSGSAMP1	8	MAP	SMED map for MSGSample display file output	2025-07-28 10:00:00	2025-07-28 10:00:00	1.0
117	BROWSE_MENU	8	MAP	SMED architecture compliant browsing map with proper ITEM field definitions and Japanese text support	2025-07-28 18:00:00	2025-07-28 18:00:00	1.0
118	LOGO	8	MAP	SMED map: LOGO - OpenASP logo display map	2025-08-03 12:00:00	2025-08-03 12:00:00	1.0
119	ENDUROASP_LOGO	8	MAP	SMED map: ENDUROASP_LOGO - Enduro ASP logo display map	2025-08-03 12:00:00	2025-08-03 12:00:00	1.0
120	SAM001	9	LAYOUT	LAYOUT: SAM001 - Sequential Access Method layout definition	2025-08-03 12:05:00	2025-08-03 12:05:00	1.0
121	DAILY_BACKUP	10	JOB	Daily backup job	2025-07-21 10:00:00	2025-07-21 10:00:00	1.0
122	SCHEMA.TEST	11	DATASET	Converted from EBCDIC (JAK)	\N	2025-08-05 08:07:33.269728	1.0
123	TESTDS	12	DATASET		\N	\N	1.0
124	CONVERTED.DATA	13	DATASET		\N	\N	1.0
\.


--
-- Data for Name: programs; Type: TABLE DATA; Schema: aspuser; Owner: aspuser
--

COPY aspuser.programs (program_id, object_id, pgm_type, pgm_name, class_file, source_file, jar_file, shell_file, executable, main_method, asp_ready, japanese_support, naming_convention, execution_mode, dependencies, original_source, encoding) FROM stdin;
1	5	JAVA	com.openasp.menu.MainMenu	\N	\N	menu-programs.jar	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
2	6	JAVA	PRT001	PRT001.class	PRT001.java	\N	\N	\N	t	f	f	\N	STANDALONE	NONE	\N	UTF-8
3	7	COBOL	PAYROLL01	\N	PAYROLL01.cbl	\N	\N	PAYROLL01	f	f	f	\N	\N	\N	\N	UTF-8
4	9	JAVA	NEWPROGRAM	\N	\N	NEWPROGRAM.jar	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
5	11	JAVA	TestProgram	\N	\N	TestProgram.jar	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
6	12	JAVA	EnhancedTestProgram	\N	\N	EnhancedTestProgram.jar	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
7	13	SHELL	test_shell.sh	\N	\N	\N	test_shell.sh	\N	f	f	f	\N	\N	\N	\N	UTF-8
8	14	JAVA	com.openasp.sample.PGM000	com/openasp/sample/PGM000.class	\N	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
9	15	JAVA	com.openasp.sample.PGM004	com/openasp/sample/PGM004.class	\N	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
10	16	JAVA	com.openasp.sample.PGM002	com/openasp/sample/PGM002.class	\N	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
11	17	JAVA	com.openasp.sample.PGM003	com/openasp/sample/PGM003.class	\N	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
12	18	JAVA	com.openasp.sample.PGM001	com/openasp/sample/PGM001.class	\N	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
13	19	JAVA	CUINP001	CUINP001.class	\N	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
14	21	SHELL	test_job.sh	\N	\N	\N	test_job.sh	\N	f	f	f	\N	\N	\N	\N	UTF-8
15	22	SHELL	long_job.sh	\N	\N	\N	long_job.sh	\N	f	f	f	\N	\N	\N	\N	UTF-8
16	23	CL	EMPINQ	\N	EMPINQ.cl	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
17	24	CL	EMPADD	\N	EMPADD.cl	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
18	25	CL	EMPUPD	\N	EMPUPD.cl	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
19	26	CL	EMPDEL	\N	EMPDEL.cl	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
20	27	CL	BACKUP	\N	BACKUP.cl	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
21	28	CL	RESTORE	\N	RESTORE.cl	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
22	29	CL	SYSCLEAN	\N	SYSCLEAN.cl	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
23	30	CL	LONGJOB	\N	LONGJOB.cl	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
24	31	CL	REPORT	\N	REPORT.cl	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
25	32	CL	FILEUTIL	\N	FILEUTIL.cl	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
26	33	JAVA	com.openasp.file.EmployeeFileProcessor	com/openasp/file/EmployeeFileProcessor.class	\N	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
27	34	CL	TESTCL	\N	TESTCL	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
28	35	CL	TESTJP_ASP	\N	TESTJP_ASP	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
29	36	JAVA	HelloASP	HelloASP.class	\N	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
30	37	JAVA	HelloASP	HelloASP.class	\N	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
31	38	CL	TESTCL1	\N	TESTCL1	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
32	39	CL	FILEUTIL_ASP	\N	FILEUTIL_ASP	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
33	40	CL	DATAPROC_ASP	\N	DATAPROC_ASP	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
34	41	CL	DAILY_BATCH	\N	DAILY_BATCH	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
35	42	CL	SYSTEM_CHECK	\N	SYSTEM_CHECK	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
36	43	CL	DATA_INIT	\N	DATA_INIT	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
37	44	CL	FILEWRITE_ASP	\N	FILEWRITE_ASP	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
38	45	CL	EMPLOYEE_WRITE	\N	EMPLOYEE_WRITE	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
39	46	CL	REPORT_WRITE	\N	REPORT_WRITE	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
40	47	CL	LOG_WRITE	\N	LOG_WRITE	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
41	48	CL	EMPREAD_CL	\N	EMPREAD_CL	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
42	49	JAVA	TESTPGM	TESTPGM.class	\N	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
43	50	JAVA	MSGSample	MSGSample.class	\N	MSGSample.jar	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
44	51	JAVA	MSGSample	MSGSample.class	\N	MSGSample.jar	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
45	53	CL	TESTMSG_CL	\N	TESTMSG_CL	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
46	54	JAVA	MSGSampleBrowserMenuClean	MSGSampleBrowserMenuClean.class	\N	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
47	55	JAVA	MSGSampleBrowserMenuJSON	MSGSampleBrowserMenuJSON.class	\N	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
48	71	CL	CL001	\N	CL001	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
49	72	CL	CLTEST01	\N	CLTEST01	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
50	74	JAVA	MAIN001	MAIN001.class	MAIN001.java	\N	\N	\N	t	t	t	8BYTE	STANDALONE	NONE	MAIN001.cob	UTF-8
51	75	JAVA	MAIN001Demo	MAIN001Demo.class	MAIN001Demo.java	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
52	76	JAVA	SimpleMAIN001Test	SimpleMAIN001Test.class	SimpleMAIN001Test.java	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
53	77	JAVA	TSTJAVA1	TSTJAVA1.class	TSTJAVA1.java	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
54	78	JAVA	TestAbend	TestAbend.class	TestAbend.java	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
55	79	JAVA	com.openasp.common.JSONResponse	com/openasp/common/JSONResponse.class	JSONResponse.java	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
56	80	JAVA	com.openasp.sub.SUB001	com/openasp/sub/SUB001.class	SUB001.java	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
57	81	JAVA	com.openasp.main.MAIN001	com/openasp/main/MAIN001.class	MAIN001.java	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
58	82	JAVA	com.openasp.main.DisplayOutputHandler	com/openasp/main/DisplayOutputHandler.class	DisplayOutputHandler.java	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
59	83	JAVA	com.openasp.main.MAIN001Interactive	com/openasp/main/MAIN001Interactive.class	MAIN001Interactive.java	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
60	84	JAVA	com.openasp.main.MAIN001Test	com/openasp/main/MAIN001Test.class	MAIN001Test.java	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
61	85	JAVA	com.openasp.main.CobolFileException	com/openasp/main/CobolFileException.class	CobolFileException.java	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
62	86	JAVA	com.openasp.main.MitdspRecord	com/openasp/main/MitdspRecord.class	MitdspRecord.java	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
63	87	JAVA	com.openasp.main.OutputHandler	com/openasp/main/OutputHandler.class	OutputHandler.java	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
64	88	JAVA	com.openasp.main.DspFile	com/openasp/main/DspFile.class	DspFile.java	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
65	89	JAVA	com.openasp.main.CobolDataConversionException	com/openasp/main/CobolDataConversionException.class	CobolDataConversionException.java	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
66	90	JAVA	com.openasp.main.WebUIService	com/openasp/main/WebUIService.class	WebUIService.java	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
67	93	SHELL	billing.sh	\N	\N	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
68	96	CL	TESTCL	\N	TESTCL	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
69	97	CL	BACKUP_ASP	\N	BACKUP_ASP	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
70	98	CL	REPORT_ASP	\N	REPORT_ASP	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
71	99	CL	CLEANUP_ASP	\N	CLEANUP_ASP	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
72	100	CL	LONGRUN_ASP	\N	LONGRUN_ASP	\N	\N	\N	f	f	f	\N	\N	\N	\N	UTF-8
73	103	JAVA	MAIN001	MAIN001.class	MAIN001.java	\N	\N	\N	t	t	t	8BYTE	STANDALONE	NONE	MAIN001.cob	UTF-8
74	104	JAVA	com.openasp.sub.SUB001	com/openasp/sub/SUB001.class	SUB001.java	\N	\N	\N	t	t	t	8BYTE	STANDALONE	NONE	SUB001.cob	UTF-8
75	105	JAVA	TSTJAVA1	TSTJAVA1.class	TSTJAVA1.java	\N	\N	\N	t	t	f	\N	STANDALONE	NONE	\N	UTF-8
\.


--
-- Data for Name: volumes; Type: TABLE DATA; Schema: aspuser; Owner: aspuser
--

COPY aspuser.volumes (volume_id, volume_name, description, created_at, updated_at) FROM stdin;
2	DISK01	OpenASP Volume: DISK01	2025-09-01 05:24:24.383895	2025-09-01 05:24:24.383895
3	DISK02	OpenASP Volume: DISK02	2025-09-01 05:24:24.383895	2025-09-01 05:24:24.383895
4	TEST	OpenASP Volume: TEST	2025-09-01 05:24:24.383895	2025-09-01 05:24:24.383895
5	TEST_VOLUME	OpenASP Volume: TEST_VOLUME	2025-09-01 05:24:24.383895	2025-09-01 05:24:24.383895
\.


--
-- Name: copybooks_copybook_id_seq; Type: SEQUENCE SET; Schema: aspuser; Owner: aspuser
--

SELECT pg_catalog.setval('aspuser.copybooks_copybook_id_seq', 2, true);


--
-- Name: dataset_conversions_conversion_id_seq; Type: SEQUENCE SET; Schema: aspuser; Owner: aspuser
--

SELECT pg_catalog.setval('aspuser.dataset_conversions_conversion_id_seq', 13, true);


--
-- Name: datasets_dataset_id_seq; Type: SEQUENCE SET; Schema: aspuser; Owner: aspuser
--

SELECT pg_catalog.setval('aspuser.datasets_dataset_id_seq', 26, true);


--
-- Name: jobs_job_id_seq; Type: SEQUENCE SET; Schema: aspuser; Owner: aspuser
--

SELECT pg_catalog.setval('aspuser.jobs_job_id_seq', 1, true);


--
-- Name: layouts_layout_id_seq; Type: SEQUENCE SET; Schema: aspuser; Owner: aspuser
--

SELECT pg_catalog.setval('aspuser.layouts_layout_id_seq', 1, true);


--
-- Name: libraries_library_id_seq; Type: SEQUENCE SET; Schema: aspuser; Owner: aspuser
--

SELECT pg_catalog.setval('aspuser.libraries_library_id_seq', 13, true);


--
-- Name: maps_map_id_seq; Type: SEQUENCE SET; Schema: aspuser; Owner: aspuser
--

SELECT pg_catalog.setval('aspuser.maps_map_id_seq', 16, true);


--
-- Name: objects_object_id_seq; Type: SEQUENCE SET; Schema: aspuser; Owner: aspuser
--

SELECT pg_catalog.setval('aspuser.objects_object_id_seq', 124, true);


--
-- Name: programs_program_id_seq; Type: SEQUENCE SET; Schema: aspuser; Owner: aspuser
--

SELECT pg_catalog.setval('aspuser.programs_program_id_seq', 75, true);


--
-- Name: volumes_volume_id_seq; Type: SEQUENCE SET; Schema: aspuser; Owner: aspuser
--

SELECT pg_catalog.setval('aspuser.volumes_volume_id_seq', 5, true);


--
-- Name: copybooks copybooks_object_id_unique; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.copybooks
    ADD CONSTRAINT copybooks_object_id_unique UNIQUE (object_id);


--
-- Name: copybooks copybooks_pkey; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.copybooks
    ADD CONSTRAINT copybooks_pkey PRIMARY KEY (copybook_id);


--
-- Name: dataset_conversions dataset_conversions_dataset_id_unique; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.dataset_conversions
    ADD CONSTRAINT dataset_conversions_dataset_id_unique UNIQUE (dataset_id);


--
-- Name: dataset_conversions dataset_conversions_pkey; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.dataset_conversions
    ADD CONSTRAINT dataset_conversions_pkey PRIMARY KEY (conversion_id);


--
-- Name: datasets datasets_object_id_unique; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.datasets
    ADD CONSTRAINT datasets_object_id_unique UNIQUE (object_id);


--
-- Name: datasets datasets_pkey; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.datasets
    ADD CONSTRAINT datasets_pkey PRIMARY KEY (dataset_id);


--
-- Name: jobs jobs_object_id_unique; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.jobs
    ADD CONSTRAINT jobs_object_id_unique UNIQUE (object_id);


--
-- Name: jobs jobs_pkey; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (job_id);


--
-- Name: layouts layouts_object_id_unique; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.layouts
    ADD CONSTRAINT layouts_object_id_unique UNIQUE (object_id);


--
-- Name: layouts layouts_pkey; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.layouts
    ADD CONSTRAINT layouts_pkey PRIMARY KEY (layout_id);


--
-- Name: libraries libraries_pkey; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.libraries
    ADD CONSTRAINT libraries_pkey PRIMARY KEY (library_id);


--
-- Name: libraries libraries_volume_id_library_name_key; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.libraries
    ADD CONSTRAINT libraries_volume_id_library_name_key UNIQUE (volume_id, library_name);


--
-- Name: maps maps_object_id_unique; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.maps
    ADD CONSTRAINT maps_object_id_unique UNIQUE (object_id);


--
-- Name: maps maps_pkey; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.maps
    ADD CONSTRAINT maps_pkey PRIMARY KEY (map_id);


--
-- Name: objects objects_library_id_object_name_key; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.objects
    ADD CONSTRAINT objects_library_id_object_name_key UNIQUE (library_id, object_name);


--
-- Name: objects objects_pkey; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.objects
    ADD CONSTRAINT objects_pkey PRIMARY KEY (object_id);


--
-- Name: programs programs_object_id_unique; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.programs
    ADD CONSTRAINT programs_object_id_unique UNIQUE (object_id);


--
-- Name: programs programs_pkey; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.programs
    ADD CONSTRAINT programs_pkey PRIMARY KEY (program_id);


--
-- Name: volumes volumes_pkey; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.volumes
    ADD CONSTRAINT volumes_pkey PRIMARY KEY (volume_id);


--
-- Name: volumes volumes_volume_name_key; Type: CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.volumes
    ADD CONSTRAINT volumes_volume_name_key UNIQUE (volume_name);


--
-- Name: idx_copybooks_object; Type: INDEX; Schema: aspuser; Owner: aspuser
--

CREATE INDEX idx_copybooks_object ON aspuser.copybooks USING btree (object_id);


--
-- Name: idx_datasets_object; Type: INDEX; Schema: aspuser; Owner: aspuser
--

CREATE INDEX idx_datasets_object ON aspuser.datasets USING btree (object_id);


--
-- Name: idx_jobs_object; Type: INDEX; Schema: aspuser; Owner: aspuser
--

CREATE INDEX idx_jobs_object ON aspuser.jobs USING btree (object_id);


--
-- Name: idx_layouts_object; Type: INDEX; Schema: aspuser; Owner: aspuser
--

CREATE INDEX idx_layouts_object ON aspuser.layouts USING btree (object_id);


--
-- Name: idx_libraries_volume; Type: INDEX; Schema: aspuser; Owner: aspuser
--

CREATE INDEX idx_libraries_volume ON aspuser.libraries USING btree (volume_id);


--
-- Name: idx_maps_object; Type: INDEX; Schema: aspuser; Owner: aspuser
--

CREATE INDEX idx_maps_object ON aspuser.maps USING btree (object_id);


--
-- Name: idx_objects_library; Type: INDEX; Schema: aspuser; Owner: aspuser
--

CREATE INDEX idx_objects_library ON aspuser.objects USING btree (library_id);


--
-- Name: idx_objects_type; Type: INDEX; Schema: aspuser; Owner: aspuser
--

CREATE INDEX idx_objects_type ON aspuser.objects USING btree (object_type);


--
-- Name: idx_programs_object; Type: INDEX; Schema: aspuser; Owner: aspuser
--

CREATE INDEX idx_programs_object ON aspuser.programs USING btree (object_id);


--
-- Name: libraries update_libraries_updated_at; Type: TRIGGER; Schema: aspuser; Owner: aspuser
--

CREATE TRIGGER update_libraries_updated_at BEFORE UPDATE ON aspuser.libraries FOR EACH ROW EXECUTE FUNCTION aspuser.update_updated_at_column();


--
-- Name: objects update_objects_updated_at; Type: TRIGGER; Schema: aspuser; Owner: aspuser
--

CREATE TRIGGER update_objects_updated_at BEFORE UPDATE ON aspuser.objects FOR EACH ROW EXECUTE FUNCTION aspuser.update_updated_at_column();


--
-- Name: volumes update_volumes_updated_at; Type: TRIGGER; Schema: aspuser; Owner: aspuser
--

CREATE TRIGGER update_volumes_updated_at BEFORE UPDATE ON aspuser.volumes FOR EACH ROW EXECUTE FUNCTION aspuser.update_updated_at_column();


--
-- Name: copybooks copybooks_object_id_fkey; Type: FK CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.copybooks
    ADD CONSTRAINT copybooks_object_id_fkey FOREIGN KEY (object_id) REFERENCES aspuser.objects(object_id) ON DELETE CASCADE;


--
-- Name: dataset_conversions dataset_conversions_dataset_id_fkey; Type: FK CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.dataset_conversions
    ADD CONSTRAINT dataset_conversions_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES aspuser.datasets(dataset_id) ON DELETE CASCADE;


--
-- Name: datasets datasets_object_id_fkey; Type: FK CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.datasets
    ADD CONSTRAINT datasets_object_id_fkey FOREIGN KEY (object_id) REFERENCES aspuser.objects(object_id) ON DELETE CASCADE;


--
-- Name: jobs jobs_object_id_fkey; Type: FK CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.jobs
    ADD CONSTRAINT jobs_object_id_fkey FOREIGN KEY (object_id) REFERENCES aspuser.objects(object_id) ON DELETE CASCADE;


--
-- Name: layouts layouts_object_id_fkey; Type: FK CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.layouts
    ADD CONSTRAINT layouts_object_id_fkey FOREIGN KEY (object_id) REFERENCES aspuser.objects(object_id) ON DELETE CASCADE;


--
-- Name: libraries libraries_volume_id_fkey; Type: FK CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.libraries
    ADD CONSTRAINT libraries_volume_id_fkey FOREIGN KEY (volume_id) REFERENCES aspuser.volumes(volume_id) ON DELETE CASCADE;


--
-- Name: maps maps_object_id_fkey; Type: FK CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.maps
    ADD CONSTRAINT maps_object_id_fkey FOREIGN KEY (object_id) REFERENCES aspuser.objects(object_id) ON DELETE CASCADE;


--
-- Name: objects objects_library_id_fkey; Type: FK CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.objects
    ADD CONSTRAINT objects_library_id_fkey FOREIGN KEY (library_id) REFERENCES aspuser.libraries(library_id) ON DELETE CASCADE;


--
-- Name: programs programs_object_id_fkey; Type: FK CONSTRAINT; Schema: aspuser; Owner: aspuser
--

ALTER TABLE ONLY aspuser.programs
    ADD CONSTRAINT programs_object_id_fkey FOREIGN KEY (object_id) REFERENCES aspuser.objects(object_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

