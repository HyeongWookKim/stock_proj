CREATE TABLE cmpy_affiliate (
    bas_dt CHAR(8) NOT NULL,               -- 기준일자 (YYYYMMDD)
    crno CHAR(13) NOT NULL,                -- 법인등록번호 (NOT NULL)
    afil_cmpy_nm VARCHAR(1000) NOT NULL,   -- 계열회사명 (NOT NULL)
    afil_cmpy_crno CHAR(13),               -- 계열회사법인등록번호
    lstg_yn CHAR(1)                        -- 상장여부
);