CREATE TABLE stock_price_info (
    bas_dt        CHAR(8),          -- 기준일자 (YYYYMMDD)
    srtn_cd       VARCHAR(9),       -- 단축코드
    isin_cd       VARCHAR(12),      -- ISIN 코드
    itms_nm       VARCHAR(120),     -- 종목명
    mrkt_ctg      VARCHAR(40),      -- 시장구분
    clpr          DECIMAL(12,0),    -- 종가
    vs            DECIMAL(10,0),    -- 대비
    flt_rt        DECIMAL(11,2),    -- 등락률
    mkp           DECIMAL(12,0),    -- 시가
    hipr          DECIMAL(12,0),    -- 고가
    lopr          DECIMAL(12,0),    -- 저가
    trqu          DECIMAL(12,0),    -- 거래량
    tr_prc        DECIMAL(21,0),    -- 거래대금
    lstg_st_cnt   DECIMAL(15,0),    -- 상장주식수
    mrkt_tot_amt  DECIMAL(21,0)     -- 시가총액
);