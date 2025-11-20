import os
import re
# import json
# import pprint
import logging
import requests
import traceback
import numpy as np
import pandas as pd

import psycopg2
# import pyodbc
# from sqlalchemy import create_engine
# from fast_to_sql import fast_to_sql


##### For logging #####
''' [logging]
    1. DEBUG: 상세한 정보
    2. INFO: 일반적인 정보
    3. WARNING: 경고 메세지
    4. ERROR: 에러 메세지
    5. CRITICAL: 심각한 오류
'''
logger = logging.getLogger(__name__) # 모듈 별 logger 생성 시, 주로 사용 (단일 스크립트에 적용해도 무방)
logging.basicConfig(
    filename = './logs/getDataByApi.log', 
    level = logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

##### Custom Functions #####
def camel_to_snake(name):
    '''
        Camel Case / lower Camel Case -> Snake Case로 변환
    '''
    # 첫 글자가 대문자인 Pascal Case도 처리 가능
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    # 여러 대문자 연속 처리
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()


def get_api_key(target, encoding = True):
    '''
        target: 대상 정보 명(ex. 기업기본정보, 기업재무정보, 주식시세정보, ...)
        encoding: 인코딩 된 API key 사용 여부 (False = decoding 된 값 사용)
    '''
    with open('./docs/금융위원회_OpenAPI_Keys.txt', 'r', encoding = 'utf-8') as f:
        lines = [line.strip() for line in f.readlines()]

    found_target = False
    key_type = 'Encoding' if encoding else 'Decoding'
    for line in lines:
        if target in line:
            found_target = True
            continue

        if found_target:
            if line.startswith(key_type + ':'):
                return line.split(':')[1].strip()
            
            if line and any(code in line for code in ['Encoding', 'Decoding']) is False and '.' in line:
                break

    raise ValueError(f'Target "{target}" not found or key type is missing')


def get_resp_and_insert_data(url, params, conn, table_name):
    while True:
        if IS_TEST and params['pageNo'] > 10: # 테스트인 경우, 1 ~ 10페이지 데이터만 조회 (1000 rows per each page)
            break

        resp = requests.get(url, params = params)
        logger.info(resp.url)
        if resp.status_code != 200:
            logger.error(f'>> Code: {resp.status_code}')
            logger.error(f'>> Err Msg: {resp.text}')
            return 'Cannot get response from API'

        try:
            data = resp.json()
            items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])

            if not items:
                break
                
            df_result = pd.DataFrame(items)

            # OpenAPI로 받아온 데이터 자체적으로 컬럼 명이 가이드와 다르거나 타입을 수동 지정해줘야 하는 경우들이 존재함
            if 'sbrdEnpadr' in df_result.columns:
                df_result.rename(columns = {'sbrdEnpadr': 'sbrdEnpAdr'}, inplace = True)
            if 'enp_pn1_avg_slry_amt' in df_result.columns:
                df_result['enp_pn1_avg_slry_amt'] = df_result['enp_pn1_avg_slry_amt'].astype(float) # String to float
            
            df_result.columns = [camel_to_snake(col) for col in df_result.columns] # Camel Case / lower Camel Case -> Snake Case
            # print(df_result.info()) # For check
            # print(df_result.head(2)) # For check

            # Insert data into DB
            status = insert_data(df_result, conn, table_name)
            logger.info(f"[Page {params['pageNo']}] - {status}")

            params['pageNo'] += 1

        except Exception as e:
            err_msg = e
            logger.error(f'>> Err Msg: {err_msg}')
            logger.error(traceback.format_exc())
            logger.error('>> Cannot get data from response')
            continue

    return status


def insert_data(df, conn, table_name):
    if df.empty:
        return f'No data to insert into "{table_name}" table'

    columns = df.columns.tolist()
    columns_str = ', '.join(columns)
    values_placeholder = ', '.join(['%s'] * len(columns))
    data_tuples = [tuple(x) for x in df.to_numpy()]

    cur = conn.cursor()
    query = f'''
        INSERT INTO {table_name} ({columns_str}) VALUES ({values_placeholder})
    '''
    cur.executemany(query, data_tuples)
    conn.commit()
    return f'Completed to insert {len(df)} rows into "{table_name}" table'


if __name__ == '__main__':
    # Test 실행 여부
    IS_TEST = True

    # For Check
    print('>> Starting Process..')

    try:
        # PostgreSQL Connection
        host = 'localhost'
        port = 5432
        database = 'finance'
        username = 'postgres'
        password = 'admin'
        conn = psycopg2.connect(
            host = host,
            port = port,
            database = database,
            user = username,
            password = password
        )

        NUM_OF_ROWS = 1000 # numOfRows 인자 값은 모두 동일하게 1000으로 설정
        PAGE_NO = 1 # 페이지 초깃값은 1로 설정

        # 발급 받은 API Key 가져오기 -> Decoding 된 인증키 사용
        # Encoding 된 인증키 사용 시, 인증키가 중간에 자동 변환되는 문제가 발생함
        CMPY_INFO_API_KEY = get_api_key('기업기본정보', encoding = False)
        FINANCE_STAT_API_KEY = get_api_key('기업재무정보', encoding = False)
        STOCK_PRICE_API_KEY = get_api_key('주식시세정보', encoding = False)
        STOCK_DIV_API_KEY = get_api_key('주식배당정보', encoding = False)
        STOCK_ISSUE_API_KEY = get_api_key('주식발행정보', encoding = False)

        ####################################################################################################

        ### 1. 금융위원회 - 기업기본정보  ###
        print('>> Starting to collect "Company Info" data by OpenAPI..')
        cmpy_info_url = 'http://apis.data.go.kr/1160100/service/GetCorpBasicInfoService_V2/'

        ## 상세기능 목록 ##
        # 1)  기업 개요 조회
        overview_url = cmpy_info_url + 'getCorpOutline_V2'
        overview_params = {
            'numOfRows': NUM_OF_ROWS, # 한 페이지 결과 수
            'pageNo': PAGE_NO, # 페이지 번호
            'resultType': 'json',
            # 'crno': , # 법인등록번호 (Optional)
            # 'corpNm': , # 법인명 (Optional)
            'serviceKey': CMPY_INFO_API_KEY
        }

        # 2) 계열 회사 조회
        afil_cmpy_url = cmpy_info_url + 'getAffiliate_V2'
        afil_cmpy_params = {
            'numOfRows': NUM_OF_ROWS, # 한 페이지 결과 수
            'pageNo': PAGE_NO, # 페이지 번호
            'resultType': 'json',
            # 'basDt': , # 작업 또는 거래의 기준이 되는 일자(년월일=yyyymmdd) (Optional)
            # 'crno': , # 법인등록번호 (Optional)
            # 'afilCmpyNm': , # 계열 회사명 (Optional)
            'serviceKey': CMPY_INFO_API_KEY
        }

        # 3) 연결대상 종속기업 조회
        sbrd_enp_url = cmpy_info_url + 'getConsSubsComp_V2'
        sbrd_enp_params = {
            'numOfRows': NUM_OF_ROWS, # 한 페이지 결과 수
            'pageNo': PAGE_NO, # 페이지 번호
            'resultType': 'json',
            # 'basDt': , # 작업 또는 거래의 기준이 되는 일자(년월일=yyyymmdd) (Optional)
            # 'crno': , # 법인등록번호 (Optional)
            # 'sbrdEnpNm': , # 종속기업명 (Optional)
            'serviceKey': CMPY_INFO_API_KEY
        }

        # 기업기본정보 데이터
        status = get_resp_and_insert_data(overview_url, overview_params, conn, 'cmpy_overview')
        status = get_resp_and_insert_data(afil_cmpy_url, afil_cmpy_params, conn, 'cmpy_affiliate')
        status = get_resp_and_insert_data(sbrd_enp_url, sbrd_enp_params, conn, 'cmpy_subsidiary')

        print('>> Completed to collect "Company Info" data by OpenAPI!')

        ####################################################################################################

        ### 2. 금융위원회 - 기업재무정보  ###
        print('>> Starting to collect "Company Finance" data by OpenAPI..')
        finance_stat_url = 'http://apis.data.go.kr/1160100/service/GetFinaStatInfoService_V2/'

        ## 상세기능 목록 ##
        # 1)  요약재무제표 조회
        summ_fina_stat_url = finance_stat_url + 'getSummFinaStat_V2'
        summ_fina_stat_params = {
            'numOfRows': NUM_OF_ROWS, # 한 페이지 결과 수
            'pageNo': PAGE_NO, # 페이지 번호
            'resultType': 'json',
            # 'crno': , # 법인등록번호 (Optional)
            # 'bizYear': , # 사업연도(yyyy): 법인에 대해 법령이 규정한 1회계기간으로서 법인세의 과세기간 (Optional)
            'serviceKey': FINANCE_STAT_API_KEY
        }

        # 2) 재무상태표 조회
        bs_url = finance_stat_url + 'getBs_V2'
        bs_params = {
            'numOfRows': NUM_OF_ROWS, # 한 페이지 결과 수
            'pageNo': PAGE_NO, # 페이지 번호
            'resultType': 'json',
            # 'crno': , # 법인등록번호 (Optional)
            # 'bizYear': , # 사업연도(yyyy): 법인에 대해 법령이 규정한 1회계기간으로서 법인세의 과세기간 (Optional)
            'serviceKey': FINANCE_STAT_API_KEY
        }

        # 3) 손익계산서 조회
        inco_stat_url = finance_stat_url + 'getIncoStat_V2'
        inco_stat_params = {
            'numOfRows': NUM_OF_ROWS, # 한 페이지 결과 수
            'pageNo': PAGE_NO, # 페이지 번호
            'resultType': 'json',
            # 'crno': , # 법인등록번호 (Optional)
            # 'bizYear': , # 사업연도(yyyy): 법인에 대해 법령이 규정한 1회계기간으로서 법인세의 과세기간 (Optional)
            'serviceKey': FINANCE_STAT_API_KEY
        }

        # 기업재무정보 데이터
        status = get_resp_and_insert_data(summ_fina_stat_url, summ_fina_stat_params, conn, 'summ_finance_stat')
        status = get_resp_and_insert_data(bs_url, bs_params, conn, 'balance_sheet')
        status = get_resp_and_insert_data(inco_stat_url, inco_stat_params, conn, 'income_stat')

        print('>> Completed to collect "Company Finance" data by OpenAPI!')

        ####################################################################################################

        ### 3. 금융위원회 - 주식시세정보  ###
        print('>> Starting to collect "Stock Price" data by OpenAPI..')
        stock_price_url = 'https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/'

        ## 상세기능 목록 ##
        # 1)  주식시세 조회
        stock_price_info_url = stock_price_url + 'getStockPriceInfo'
        stock_price_info_params = {
            'numOfRows': NUM_OF_ROWS, # 한 페이지 결과 수
            'pageNo': PAGE_NO, # 페이지 번호
            'resultType': 'json',
            # 'basDt': , # 기준일자: 검색 값과 기준일자가 일치하는 데이터를 검색 (Optional)
            # 'beginBasDt': , # 기준일자: 기준일자가 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endBasDt': , # 기준일자: 기준일자가 검색 값보다 작은 데이터를 검색 (Optional)
            # 'likeBasDt': , # 기준일자: 기준일자가 검색 값을 포함하는 데이터를 검색 (Optional)
            # 'likeSrtnCd': , # 단축코드: 단축코드가 검색 값을 포함하는 데이터를 검색 (Optional)
            # 'isinCd': , # ISIN코드: 검색 값과 ISIN코드가 일치하는 데이터를 검색 (Optional)
            # 'likeIsinCd': , # ISIN코드: ISIN코드가 검색 값을 포함하는 데이터를 검색 (Optional)
            # 'itmsNm': , # 종목명: 검색 값과 종목명이 일치하는 데이터를 검색 (Optional)
            # 'likeItmsNm': , # 종목명: 종목명이 검색 값을 포함하는 데이터를 검색 (Optional)
            # 'mrktCls': , # 시장구분: 검색 값과 시장구분이 일치하는 데이터를 검색 (Optional)
            # 'beginVs': , # 대비: 대비가 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endVs': , # 대비: 대비가 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginFltRt': , # 등락률: 등락률이 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endFltRt': , # 등락률: 등락률이 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginTrqu': , # 거래량: 거래량이 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endTrqu': , # 거래량: 거래량이 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginTrPrc': , # 거래대금: 거래대금이 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endTrPrc': , # 거래대금: 거래대금이 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginLstgStCnt': , # 상장주식수: 상장주식수가 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endLstgStCnt': , # 상장주식수: 상장주식수가 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginMrktTotAmt': , # 시가총액: 시가총액이 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endMrktTotAmt': , # 시가총액: 시가총액이 검색 값보다 작은 데이터를 검색 (Optional)
            'serviceKey': STOCK_PRICE_API_KEY
        }

        # 2) 신주인수권증서시세 조회
        prempt_right_crtf_price_url = stock_price_url + 'getPreemptiveRightCertificatePriceInfo'
        prempt_right_crtf_price_params = {
            'numOfRows': NUM_OF_ROWS, # 한 페이지 결과 수
            'pageNo': PAGE_NO, # 페이지 번호
            'resultType': 'json',
            # 'basDt': , # 기준일자: 검색 값과 기준일자가 일치하는 데이터를 검색 (Optional)
            # 'beginBasDt': , # 기준일자: 기준일자가 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endBasDt': , # 기준일자: 기준일자가 검색 값보다 작은 데이터를 검색 (Optional)
            # 'likeBasDt': , # 기준일자: 기준일자가 검색 값을 포함하는 데이터를 검색 (Optional)
            # 'likeSrtnCd': , # 단축코드: 단축코드가 검색 값을 포함하는 데이터를 검색 (Optional)
            # 'isinCd': , # ISIN코드: 검색 값과 ISIN코드가 일치하는 데이터를 검색 (Optional)
            # 'likeIsinCd': , # ISIN코드: ISIN코드가 검색 값을 포함하는 데이터를 검색 (Optional)
            # 'itmsNm': , # 종목명: 검색 값과 종목명이 일치하는 데이터를 검색 (Optional)
            # 'likeItmsNm': , # 종목명: 종목명이 검색 값을 포함하는 데이터를 검색 (Optional)
            # 'mrktCtg': , # 시장구분: 검색 값과 시장구분 값이 일치하는 데이터를 검색 (Optional)
            # 'beginVs': , # 대비: 대비가 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endVs': , # 대비: 대비가 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginFltRt': , # 등락률: 등락률이 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endFltRt': , # 등락률: 등락률이 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginTrqu': , # 거래량: 거래량이 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endTrqu': , # 거래량: 거래량이 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginTrPrc': , # 거래대금: 거래대금이 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endTrPrc': , # 거래대금: 거래대금이 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginMrktTotAmt': , # 시가총액: 시가총액이 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endMrktTotAmt': , # 시가총액: 시가총액이 검색 값보다 작은 데이터를 검색 (Optional)
            # 'likePurRgtScrtItmsCd': , # 목적주권_종목코드: 목적주권_종목코드가 검색 값을 포함하는 데이터를 검색 (Optional)
            # 'purRgtScrtItmsNm': , # 목적주권_종목명: 목적주권_종목명이 검색 값과 일치하는 데이터를 검색 (Optional)
            # 'likePurRgtScrtItmsNm': , # 목적주권_종목명: 목적주권_종목명이 검색 값을 포함하는 데이터를 검색 (Optional)
            'serviceKey': STOCK_PRICE_API_KEY
        }

        # 3) 수익증권시세 조회
        secure_price_info_url = stock_price_url + 'getSecuritiesPriceInfo'
        secure_price_info_params = {
            'numOfRows': NUM_OF_ROWS, # 한 페이지 결과 수
            'pageNo': PAGE_NO, # 페이지 번호
            'resultType': 'json',
            # 'basDt': , # 기준일자: 검색 값과 기준일자가 일치하는 데이터를 검색 (Optional)
            # 'beginBasDt': , # 기준일자: 기준일자가 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endBasDt': , # 기준일자: 기준일자가 검색 값보다 작은 데이터를 검색 (Optional)
            # 'likeBasDt': , # 기준일자: 기준일자가 검색 값을 포함하는 데이터를 검색 (Optional)
            # 'likeSrtnCd': , # 단축코드: 단축코드가 검색 값을 포함하는 데이터를 검색 (Optional)
            # 'isinCd': , # ISIN코드: 검색 값과 ISIN코드가 일치하는 데이터를 검색 (Optional)
            # 'likeIsinCd': , # ISIN코드: ISIN코드가 검색 값을 포함하는 데이터를 검색 (Optional)
            # 'itmsNm': , # 종목명: 검색 값과 종목명이 일치하는 데이터를 검색 (Optional)
            # 'likeItmsNm': , # 종목명: 종목명이 검색 값을 포함하는 데이터를 검색 (Optional)
            # 'beginVs': , # 대비: 대비가 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endVs': , # 대비: 대비가 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginFltRt': , # 등락률: 등락률이 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endFltRt': , # 등락률: 등락률이 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginTrqu': , # 거래량: 거래량이 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endTrqu': , # 거래량: 거래량이 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginTrPrc': , # 거래대금: 거래대금이 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endTrPrc': , # 거래대금: 거래대금이 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginStLstgCnt': , # 상장좌수: 상장좌수가 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endStLstgCnt': , # 상장좌수: 상장좌수가 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginMrktTotAmt': , # 시가총액: 시가총액이 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endMrktTotAmt': , # 시가총액: 시가총액이 검색 값보다 작은 데이터를 검색 (Optional)
            'serviceKey': STOCK_PRICE_API_KEY
        }

        # 4) 신주인수권증권시세 조회
        prempt_right_secure_price_url = stock_price_url + 'getPreemptiveRightSecuritiesPriceInfo'
        prempt_right_secure_price_params = {
            'numOfRows': NUM_OF_ROWS, # 한 페이지 결과 수
            'pageNo': PAGE_NO, # 페이지 번호
            'resultType': 'json',
            # 'basDt': , # 기준일자: 검색 값과 기준일자가 일치하는 데이터를 검색 (Optional)
            # 'beginBasDt': , # 기준일자: 기준일자가 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endBasDt': , # 기준일자: 기준일자가 검색 값보다 작은 데이터를 검색 (Optional)
            # 'likeBasDt': , # 기준일자: 기준일자가 검색 값을 포함하는 데이터를 검색 (Optional)
            # 'likeSrtnCd': , # 단축코드: 단축코드가 검색 값을 포함하는 데이터를 검색 (Optional)
            # 'isinCd': , # ISIN코드: 검색 값과 ISIN코드가 일치하는 데이터를 검색 (Optional)
            # 'likeIsinCd': , # ISIN코드: ISIN코드가 검색 값을 포함하는 데이터를 검색 (Optional)
            # 'itmsNm': , # 종목명: 검색 값과 종목명이 일치하는 데이터를 검색 (Optional)
            # 'likeItmsNm': , # 종목명: 종목명이 검색 값을 포함하는 데이터를 검색 (Optional)
            # 'mrktCtg': , # 시장구분: 검색 값과 시장구분이 일치하는 데이터를 검색 (Optional)
            # 'beginVs': , # 대비: 대비가 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endVs': , # 대비: 대비가 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginFltRt': , # 등락률: 등락률이 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endFltRt': , # 등락률: 등락률이 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginTrqu': , # 거래량: 거래량이 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endTrqu': , # 거래량: 거래량이 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginTrPrc': , # 거래대금: 거래대금이 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endTrPrc': , # 거래대금: 거래대금이 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginMrktTotAmt': , # 시가총액: 시가총액이 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endMrktTotAmt': , # 시가총액: 시가총액이 검색 값보다 작은 데이터를 검색 (Optional)
            # 'beginLstgScrtCnt': , # 상장증권수: 상장증권수가 검색 값보다 크거나 같은 데이터를 검색 (Optional)
            # 'endLstgScrtCnt': , # 상장증권수: 상장증권수가 검색 값보다 작은 데이터를 검색 (Optional)
            # 'likePurRgtScrtItmsCd': , # 목적주권_종목코드: 목적주권_종목코드가 검색 값을 포함하는 데이터를 검색 (Optional)
            # 'purRgtScrtItmsNm': , # 목적주권_종목명: 검색 값과 목적주권_종목명이 일치하는 데이터를 검색 (Optional)
            # 'likePurRgtScrtItmsNm': , # 목적주권_종목명: 목적주권_종목명이 검색 값을 포함하는 데이터를 검색 (Optional)
            'serviceKey': STOCK_PRICE_API_KEY
        }

        # 주식시세정보 데이터
        status = get_resp_and_insert_data(stock_price_info_url, stock_price_info_params, conn, 'stock_price_info')
        status = get_resp_and_insert_data(prempt_right_crtf_price_url, prempt_right_crtf_price_params, conn, 'prempt_right_crtf_price')
        status = get_resp_and_insert_data(secure_price_info_url, secure_price_info_params, conn, 'secure_price_info')
        status = get_resp_and_insert_data(prempt_right_secure_price_url, prempt_right_secure_price_params, conn, 'prempt_right_secure_price')

        print('>> Completed to collect "Stock Price" data by OpenAPI!')

    except Exception as e:
        err_msg = e
        logger.error(f'>> Err Msg: {err_msg}')
        logger.error(traceback.format_exc())
        conn.rollback()

    finally:
        conn.close()
        print('>> Completed Process!')