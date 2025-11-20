CREATE TABLE summ_finance_stat (
    bas_dt CHAR(8),
    crno VARCHAR(13) NOT NULL,
    cur_cd VARCHAR(3),
    biz_year CHAR(4) NOT NULL,
    fncl_dcd VARCHAR(35),
    fncl_dcd_nm VARCHAR(100),
    enp_sale_amt DECIMAL(22,3),
    enp_bzop_pft DECIMAL(22,3),
    icls_pal_clc_amt DECIMAL(22,3),
    enp_crtm_npf DECIMAL(22,3),
    enp_tast_amt DECIMAL(18,3),
    enp_tdbt_amt DECIMAL(18,3),
    enp_tcpt_amt DECIMAL(18,3),
    enp_cptl_amt DECIMAL(18,3),
    fncl_debt_rto DECIMAL(26,10)
);