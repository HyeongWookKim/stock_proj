CREATE TABLE cmpy_overview (
    crno CHAR(13) NOT NULL,                 -- 법인등록번호 (NOT NULL)
    corp_nm VARCHAR(1000) NOT NULL,         -- 법인명 (NOT NULL)
    corp_ensn_nm VARCHAR(1000),             -- 법인영문명
    enp_pban_cmpy_nm VARCHAR(1000),         -- 기업공시회사명
    enp_rpr_fnm VARCHAR(150),               -- 기업대표자성명
    corp_reg_mrkt_dcd CHAR(1),              -- 법인등록시장구분코드
    corp_reg_mrkt_dcd_nm VARCHAR(100),      -- 법인등록시장구분코드명
    corp_dcd CHAR(2),                       -- 법인구분코드
    corp_dcd_nm VARCHAR(100),               -- 법인구분코드명
    bzno CHAR(10) NOT NULL,                 -- 사업자등록번호 (NOT NULL)
    enp_ozpno CHAR(6),                      -- 기업구우편번호
    enp_bsadr VARCHAR(500),                 -- 기업기본주소
    enp_dtadr VARCHAR(500),                 -- 기업상세주소
    enp_hmpg_url VARCHAR(300),              -- 기업홈페이지URL
    enp_tlno VARCHAR(100),                  -- 기업전화번호
    enp_fxno VARCHAR(100),                  -- 기업팩스번호
    sic_nm VARCHAR(1000),                   -- 표준산업분류명
    enp_estb_dt CHAR(8),                    -- 기업설립일자 (YYYYMMDD)
    enp_stac_mm CHAR(2),                    -- 기업결산월
    enp_xchg_lstg_dt CHAR(8),               -- 기업거래소상장일자
    enp_xchg_lstg_abol_dt CHAR(8),          -- 기업거래소상장폐지일자
    enp_kosdaq_lstg_dt CHAR(8),             -- 기업코스닥상장일자
    enp_kosdaq_lstg_abol_dt CHAR(8),        -- 기업코스닥상장폐지일자
    enp_krx_lstg_dt CHAR(8),                -- 기업KONEX상장일자
    enp_krx_lstg_abol_dt CHAR(8),           -- 기업KONEX상장폐지일자
    smenp_yn CHAR(1),                       -- 중소기업여부
    enp_mntr_bnk_nm VARCHAR(100),           -- 기업주거래은행명
    enp_empe_cnt CHAR(9),                   -- 기업종업원수
    empe_avg_cnwk_term_ctt VARCHAR(100),    -- 종업원평균근속기간내용
    enp_pn1_avg_slry_amt DECIMAL(22,3),     -- 기업1인평균급여금액
    actn_audpn_nm VARCHAR(1000),            -- 회계감사인명
    audt_rpt_opnn_ctt VARCHAR(100),         -- 감사보고서의견내용
    enp_main_biz_nm VARCHAR(1000),          -- 기업주요사업명
    fss_corp_unq_no CHAR(8),                -- 금융감독원법인고유번호
    fss_corp_chg_dtm CHAR(10),              -- 금융감독원법인변경일시
    fst_opeg_dt CHAR(8),                    -- 최초개방일자
    last_opeg_dt CHAR(8)                    -- 최종개방일자
);