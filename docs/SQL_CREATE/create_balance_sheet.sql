CREATE TABLE balance_sheet (
    bas_dt CHAR(8),
    crno VARCHAR(13) NOT NULL,
    cur_cd VARCHAR(3),
    biz_year CHAR(4) NOT NULL,
    fncl_dcd VARCHAR(35),
    fncl_dcd_nm VARCHAR(100),
    acit_id VARCHAR(200),
    acit_nm VARCHAR(1000),
    thqr_acit_amt DECIMAL(22,3),
    crtm_acit_amt DECIMAL(22,3),
    lsqt_acit_amt DECIMAL(22,3),
    pvtr_acit_amt DECIMAL(22,3),
    bpvtr_acit_amt DECIMAL(22,3)
);