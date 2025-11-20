CREATE TABLE cmpy_subsidiary (
    bas_dt CHAR(8) NOT NULL,                        -- 기준일자 (YYYYMMDD) (NOT NULL)
    crno CHAR(13) NOT NULL,                         -- 법인등록번호 (NOT NULL)
    sbrd_enp_nm VARCHAR(150) NOT NULL,              -- 종속기업명 (NOT NULL)
    sbrd_enp_estb_dt CHAR(8),                       -- 종속기업설립일자
    sbrd_enp_adr VARCHAR(500),                      -- 종속기업주소
    sbrd_enp_main_biz_ctt VARCHAR(500),             -- 종속기업주요사업내용
    sbrd_enp_ltst_ebzyr_tast_amt DECIMAL(18,0),     -- 종속기업최근사업연도말총자산금액
    dnt_rlt_bsis_ctt VARCHAR(500),                  -- 지배관계근거내용
    main_sbrd_enp_yn_ctt VARCHAR(500)               -- 주요종속기업여부내용
);