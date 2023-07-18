import time
import chromedriver_autoinstaller
import telegram
import traceback
import logging
import datetime
import common
from selenium import webdriver
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.alert import Alert
from fake_useragent import UserAgent

# set logging
logger = logging.getLogger("daily")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s||%(name)s[%(levelname)s]\n%(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S'
                             )

# console
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
# file
log_filename = datetime.datetime.now().strftime("%Y%m%d.txt")
file_handler = logging.FileHandler(f".//log//{log_filename}", encoding="UTF-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def load_telegram():
    common.check_dir(".//", "telegram.json")
    result = common.open_json(".//", "telegram.json")
    token = result["token"]
    chatID = result["chatID"]
    return token, chatID

def open_driver():
    ua = UserAgent(verify_ssl=False)
    userAgent = ua.random

    options = webdriver.ChromeOptions()
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")
    options.add_argument(f'user-agent={userAgent}')
    options.add_argument("disable-extensions")
    options.add_argument('--log-level=3')
    options.add_argument('incognito') # 시크릿 모드
    # options.add_argument('headless')

    chromedriver_autoinstaller.install()
    driver = webdriver.Chrome(chrome_options=options)
    driver.maximize_window()
    driver.get('https://www.naver.com/')
    return driver

def login_ondisk(driver, id, pwd):
    
    ondisk = 'https://ondisk.co.kr/index.php?mode=eventMarge&sm=event&action=view&idx=746&event_page=1'
    roulette = 'https://ondisk.co.kr/event/20140409_attend/event.php?mode=eventMarge&sm=event&action=view&idx=746&event_page=1'
    
    driver.implicitly_wait(10)
    
    while 1:
        driver.get(ondisk) 
        time.sleep(5)
        login = driver.find_element('name', 'mb_id')
        login.send_keys(id)
        time.sleep(2)
        login = driver.find_element('name', 'mb_pw')
        login.send_keys(pwd)
        time.sleep(1)
        driver.find_element('xpath', '//*[@id="page-login"]/form/fieldset/div/p[3]').click()
        time.sleep(3)
        
        # alert창 꺼야함
        try:
            alert = Alert(driver)
            alert.dismiss()
        except:
            pass
        
        # 출석 룰렛 돌리기
        time.sleep(3)
        driver.get(roulette)
        time.sleep(5)
        driver.find_element('xpath', '//*[@id="js-roulette"]/p/button').click() # 룰렛 버튼 클릭
        time.sleep(2)
        
        # if already done
        try:
            alert = Alert(driver)
            alert.dismiss()
        except:
            pass
        break
    
    time.sleep(2)
    return

def login_filenori(driver, id, pwd):
    # 수정중
    site = 'https://m.filenori.com/'
    login_site = 'https://www.filenori.com/common/html/member/loginForm.html?20211001/?conn=filenori' # url 통해서 로그인시 포인트 지급
    attendance_check = 'https://m.filenori.com/noriNew/Event/eventList.do?reDirectUrl=/common/images/event/2022/20220401_attendance/event327.html?0.9969941897000485'
    attendance_check_btn = '/html/body/div[1]/div[2]/div[2]/div/div/div[4]'
    
    driver.implicitly_wait(10)
    
    try:
        driver.get(login_site) #사이트 이동
        time.sleep(5)
        
        login = driver.find_element('id', 'userID')
        login.send_keys(id)

        login = driver.find_element('id', 'userPW')
        login.send_keys(pwd)
        
        time.sleep(2)
        driver.execute_script('login_loginProc(this);')
        time.sleep(3)
        
        driver.get(site)
        time.sleep(5)
        # 출석체크 사이트 이동
        driver.get(attendance_check)
        time.sleep(2)
        driver.find_element('xpath', attendance_check_btn).click()
        time.sleep(1)
        # alert창 꺼야함
        try:
            alert = Alert(driver)
            alert.dismiss()
        except:
            pass
    except Exception as e:
        print(e)
        bot.sendMessage(chat_id = chatID, text=f'파일노리 실패 : {e}')
        return
    
    print("2 - 파일노리 출석 체크 완료")
    return
    
def login_yesfile(driver, id, pwd):
    site = 'https://www.yesfile.com/'
    roulette = 'https://www.yesfile.com/event/#tab=view&id=attendroulette'

    driver.implicitly_wait(10)                                                                                                                                                                                                                                                                                                                                     
    
    driver.get(site) #사이트 이동
    time.sleep(5)
    
    login = driver.find_element('id', 'login_userid')
    login.send_keys(id)

    login = driver.find_element('id', 'login_userpw')
    login.send_keys(pwd)

    # 로그인 버튼 클릭
    time.sleep(2)
    driver.find_element('id', 'login_btn').click()
    time.sleep(5)
    
    # 출석 체크
    while 1:
        try:
            driver.get(roulette) # 출석 사이트 이동
            time.sleep(2)
            driver.find_element('xpath', '//*[@id="attendroulette"]/button').click()
            time.sleep(2)
            break
        except:
            continue
    
    while 1:
        try:
            alert = Alert(driver)
            alert.dismiss()
            break
        except:
            continue
    return

def login_filebogo(driver, id, pwd):
    site = 'https://www.filebogo.com/'
    check = 'https://www.filebogo.com/main/event.php?doc=filebogo_attend&eventIdx=6'

    driver.implicitly_wait(10)                                                                                                                                                                                                                                                                                                                                     
    
    while 1:
        try:
            driver.get(site) #사이트 이동
            time.sleep(5)
            
            # 모달창 오늘 그만보기 스크립트 실행
            # driver.execute_script('PtnAuthEventClick("N")')
            # time.sleep(2)
            
            driver.execute_script('LgoinLayerView()')
            
            login = driver.find_element('id', 'Lay_mb_id')
            login.send_keys(id)

            login = driver.find_element('id', 'Lay_mb_pw')
            login.send_keys(pwd)
            break
            
        except Exception as e:
            continue

    # 로그인 버튼 클릭
    driver.find_element('xpath', '/html/body/div[6]/form/div[4]').click()
    time.sleep(3)
    
    driver.get(check)
    time.sleep(3)
    
    driver.execute_script('oneday_bonus()') # 출석체크 스크립트 호출
    
    time.sleep(3)
        
    while 1:
        try:
            alert = Alert(driver)
            alert.dismiss()
            break
        except:
            continue
    time.sleep(2)
    return

def inven(driver, id, pwd):
    
    #로그인
    url = 'https://member.inven.co.kr/user/scorpio/mlogin'
    
    # 출석체크
    check = 'https://imart.inven.co.kr/attendance/'
    
    # 주사위
    event01 = 'https://imart.inven.co.kr/imarble/'
    
    driver.implicitly_wait(3)                                                                                                                                                                                                                                                                                                                                     
    driver.maximize_window() #헤드리스 안쓸때
    
    while 1:
        try:
            driver.get(url) #사이트 이동
            time.sleep(3)
            
            id = "'" + id + "'"
            pwd = "'" + pwd + "'"

            driver.execute_script("document.getElementsByName('user_id')[0].value=" + id)
            time.sleep(1)
            driver.execute_script("document.getElementsByName('password')[0].value=" + pwd)
            time.sleep(1)
            break
            
        except:
            continue

    # 로그인 버튼 클릭
    driver.find_element('xpath', '//*[@id="loginBtn"]').click() # 버튼 클릭
    time.sleep(3)
    try:
        # 다음에 변경하기
        driver.find_element('xpath', '//*[@id="btn-extend"]').click() # 버튼 클릭
    except:
        pass
    time.sleep(2)
    driver.get(check) #사이트 이동
    time.sleep(3)
    driver.find_element('xpath', '//*[@id="invenAttendCheck"]/div/div[2]/div/div[3]/div[1]/div[4]/a').click() # 버튼 클릭
    time.sleep(2)
    
    # 재 로그인시
    # alert창 확인 누르기
    try:
        alert = Alert(driver)
        # alert.dismiss()
        alert.accept()
    except:
        pass
    
    # 주사위 굴리기 이벤트
    driver.get(event01)
    print("주사위 굴리기 이벤트 시작")
    time.sleep(3)
    for i in range(9):
        try:
            driver.find_element('xpath', '//*[@id="imarbleBoard"]/div[4]').click() # 버튼 클릭
            time.sleep(3)
            # alert창 확인 누르기
            # 구매하시겠습니까
            alert = Alert(driver)
            alert.accept()
            time.sleep(2)
            # 구매했습니다
            alert = Alert(driver)
            alert.accept()
            time.sleep(2)
            # 주사위돌고나면 모달창 뜸
            driver.refresh()
            time.sleep(5)
        except UnexpectedAlertPresentException as e:
            time.sleep(2)
            driver.refresh()
            pass
        except NoAlertPresentException as e:
            time.sleep(2)
            driver.refresh()
            pass
        except Exception as e:
            print(traceback.format_exc())
            pass
    
    # 결과 확인
    info1 = driver.find_element('xpath', '/html/body/div[1]/div[4]/div[1]/div[5]/div[1]').text
    info2 = driver.find_element('xpath', '/html/body/div[1]/div[4]/div[1]/div[5]/div[2]').text
    print(info1)
    print(info2)
    bot.sendMessage(chat_id = chatID, text=f'{id} / {info1} / {info2}')
    
    print("5 - 인벤 출석 체크 완료")
    
    return

def item_mania(driver, id, pwd):
    
    login = 'https://www.itemmania.com/portal/user/p_login_form.html'
    event = 'http://www.itemmania.com/event/event_ing/e190417_attend/'
                                                                                                                                                                                                                                                                                                                                  
    driver.implicitly_wait(10)
    
    while 1:
        try:
            driver.get(login)
            time.sleep(5)
            login = driver.find_element('id', 'user_id')
            login.send_keys(id)
            time.sleep(1)
            login = driver.find_element('id', 'user_password')
            login.send_keys(pwd)
            time.sleep(1)
            driver.find_element('xpath', '/html/body/div[2]/div[4]/div[2]/div[2]/form[1]/ul/li[3]/button').click()
            time.sleep(5)
            break
        except Exception as e:
            time.sleep(2)
            continue
            
    driver.get(event)
    time.sleep(5)
    
    # 안내문 끄기
    try:
        driver.find_element('xpath', '/html/body/div[1]/div[2]/div/div[1]').click()
    except:
        pass
    time.sleep(2)
    
    # 출석 버튼 누르기
    driver.find_element('xpath', '/html/body/div[2]/div[2]/div/div[3]/div/div[3]').click()
    
    # 출석 됐는지 체크
    time.sleep(3)
    check = ""
    try:
        check = driver.find_element('xpath', '/html/body/div[2]/div[2]/div/div[3]/div/div[3]').text
    except:
        bot.sendMessage(chat_id = chatID, text=f'아이템매니아 결과 파싱 실패 - 한번 더 시도')
        driver.refresh()
        time.sleep(3)
        check = driver.find_element('xpath', '/html/body/div[2]/div[2]/div/div[3]/div/div[3]').text
        
    logger.info({check})
    bot.sendMessage(chat_id = chatID, text=f'{check}')
    return


if __name__ == "__main__":
    
    account = common.open_json(".//", "personal.json")
    
    try:
        token, chatID = load_telegram()
        bot = telegram.Bot(token)
        bot.sendMessage(chat_id = chatID, text=f'daily start')
    except Exception as e:
        logger.info(f"{e} - fail to load telegram")
        
    try:
        driver = open_driver()
    except Exception as e:
        logger.info(f"{e} - fail open_driver()")
        exit()
        
    try:
        mode = "ondisk"
        login_ondisk(driver, account[mode]["id"], account[mode]["pwd"])
        logger.info(f"success {mode}")
    except Exception as e:
        logger.info(f"{e} - fail {mode}")
        
    try:
        mode = "yesfile"
        login_yesfile(driver, account[mode]["id"], account[mode]["pwd"])
        logger.info(f"success {mode}")
    except Exception as e:
        logger.info(f"{e} - fail {mode}")
        
    try:
        mode = "filebogo"
        login_filebogo(driver, account[mode]["id"], account[mode]["pwd"])
        logger.info(f"success {mode}")
    except Exception as e:
        logger.info(f"{e} - fail {mode}")
        
    try:
        mode = "inven"
        inven(driver, account[mode]["id"], account[mode]["pwd"])
        logger.info(f"success {mode}")
    except Exception as e:
        logger.info(f"{e} - fail {mode}")
        
    try:
        mode = "inven2"
        inven(driver, account[mode]["id"], account[mode]["pwd"])
        logger.info(f"success {mode}")
    except Exception as e:
        logger.info(f"{e} - fail {mode}")
        
    try:
        mode = "item_mania"
        item_mania(driver, account[mode]["id"], account[mode]["pwd"])
        logger.info(f"success {mode}")
    except Exception as e:
        logger.info(f"{e} - fail {mode}")
    
    driver.quit()
    bot.sendMessage(chat_id = chatID, text=f'daily end')