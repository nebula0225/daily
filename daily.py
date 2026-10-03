import re
import time
import html
import telegram
import traceback
import logging
import datetime
import asyncio
import common
from selenium import webdriver
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.alert import Alert
from telegram.constants import MessageLimit, ParseMode
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

# load_telegram()의 반환값을 전역 변수로 할당
TOKEN, CHAT_ID = load_telegram()

DETAIL_LIMIT = 200

def clean(text):
    """Collapse whitespace and cap length so one site cannot flood the report."""
    return " ".join(str(text).split())[:DETAIL_LIMIT]

def describe_error(e):
    # selenium appends a long native stacktrace after the first line
    lines = str(e).strip().splitlines()
    first = lines[0].removeprefix("Message: ").strip() if lines else ""
    return clean(f"{type(e).__name__}: {first}" if first else type(e).__name__)

def format_duration(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes}m{seconds:02d}s" if minutes else f"{seconds}s"

def build_report(started_at, total_seconds, results, fatal=""):
    """Build the HTML summary message from the per-site results."""
    failed = sum(not r["ok"] for r in results)
    minutes, seconds = divmod(int(total_seconds), 60)
    head = [
        f"daily {started_at:%Y-%m-%d %H:%M} (총 {minutes}분 {seconds}초)",
        f"성공 {len(results) - failed} / 실패 {failed}",
    ]
    if fatal:
        head.append(f"중단: {fatal}")

    width = max((len(r["mode"]) for r in results), default=0)
    rows = []
    for r in results:
        rows.append(f"{'OK  ' if r['ok'] else 'FAIL'} {r['mode']:<{width}}  {format_duration(r['seconds'])}")
        if r["detail"]:
            rows.append(f"     {r['detail']}")

    text = html.escape("\n".join(head))
    if rows:
        # <pre> keeps the columns aligned; plain telegram text is proportional
        text += "\n<pre>" + html.escape("\n".join(rows)) + "</pre>"
    return text

async def send_report(started_at, total_seconds, results, fatal=""):
    """Send failure screenshots silently, then the summary. Never raises."""
    try:
        async with telegram.Bot(TOKEN) as bot:
            for r in results:
                if not r["screenshot"]:
                    continue
                try:
                    await bot.send_photo(
                        chat_id=CHAT_ID,
                        photo=r["screenshot"],
                        caption=f"FAIL {r['mode']}\n{r['detail']}",
                        disable_notification=True,
                    )
                except Exception as e:
                    logger.error(f"telegram photo failed ({r['mode']}): {e}")
            text = build_report(started_at, total_seconds, results, fatal)
            try:
                await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode=ParseMode.HTML)
            except Exception as e:
                # the summary is the only message of the run, so fall back to plain text
                logger.error(f"telegram html report failed, retrying as plain text: {e}")
                plain = html.unescape(re.sub(r"</?pre>", "", text))
                await bot.send_message(chat_id=CHAT_ID, text=plain[:MessageLimit.MAX_TEXT_LENGTH])
    except Exception as e:
        logger.error(f"telegram report failed: {e}")

# retries after the first attempt; the last failure is raised so the site is reported as failed
MAX_RETRIES = 3

def open_driver():
    # ua = UserAgent(verify_ssl=False)
    # userAgent = ua.random

    options = webdriver.ChromeOptions()
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")
    # options.add_argument(f'user-agent={userAgent}')
    options.add_argument("disable-extensions")
    options.add_argument('--log-level=3')
    options.add_argument('incognito') # 시크릿 모드
    # options.add_argument('headless')

    # 자동
    # chrome_version = chromedriver_autoinstaller.get_chrome_version()
    driver = webdriver.Chrome(options=options)
    
    # 수동
    # driver = webdriver.Chrome(chrome_options=options, executable_path="chromedriver.exe")
    # logger.info(f"now chrome version : 수동")
    
    # 버전 체크
    chrome_version = driver.capabilities['browserVersion']
    print(f"now chrome version : {chrome_version}")
    logger.info(f"now chrome version : {chrome_version}")
    
    driver.maximize_window()
    driver.get('https://www.naver.com/')
    return driver

async def login_ondisk(driver, id, pwd):
    
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
        detail = ""
        try:
            alert = Alert(driver)
            detail = alert.text
            alert.dismiss()
        except:
            pass
        break

    time.sleep(2)
    return detail

async def login_filenori(driver, id, pwd):
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
        raise

    print("2 - 파일노리 출석 체크 완료")
    return
    
async def login_yesfile(driver, id, pwd):
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
    for attempt in range(MAX_RETRIES + 1):
        try:
            driver.get(roulette) # 출석 사이트 이동
            time.sleep(2)
            driver.find_element('xpath', '//*[@id="attendroulette"]/button').click()
            time.sleep(2)
            break
        except Exception:
            if attempt == MAX_RETRIES:
                raise
            continue
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            alert = Alert(driver)
            detail = alert.text
            alert.dismiss()
            break
        except Exception:
            if attempt == MAX_RETRIES:
                raise
            # give the alert time to appear before the next attempt
            time.sleep(2)
            continue
    return detail

async def login_filebogo(driver, id, pwd):
    site = 'https://www.filebogo.com/'
    check = 'https://www.filebogo.com/main/event.php?doc=filebogo_attend&eventIdx=6'

    driver.implicitly_wait(10)                                                                                                                                                                                                                                                                                                                                     
    
    for attempt in range(MAX_RETRIES + 1):
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
            if attempt == MAX_RETRIES:
                raise
            continue

    # 로그인 버튼 클릭
    driver.find_element('xpath', '/html/body/div[6]/form/div[4]').click()
    time.sleep(3)
    
    driver.get(check)
    time.sleep(3)
    
    driver.execute_script('oneday_bonus()') # 출석체크 스크립트 호출
    
    time.sleep(3)
        
    for attempt in range(MAX_RETRIES + 1):
        try:
            alert = Alert(driver)
            detail = alert.text
            alert.dismiss()
            break
        except Exception:
            if attempt == MAX_RETRIES:
                raise
            # give the alert time to appear before the next attempt
            time.sleep(2)
            continue
    time.sleep(2)
    return detail

async def inven(driver, id, pwd):
    
    #로그인
    url = 'https://member.inven.co.kr/user/scorpio/mlogin'
    
    # 출석체크
    check = 'https://imart.inven.co.kr/attendance/'
    
    # 주사위
    event01 = 'https://imart.inven.co.kr/imarble/'
    
    driver.implicitly_wait(5)
    driver.maximize_window() #헤드리스 안쓸때
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            driver.get(url) #사이트 이동
            time.sleep(5)
            
            # pass values as script arguments so quotes in them cannot break the script
            driver.execute_script("document.getElementsByName('user_id')[0].value=arguments[0]", id)
            time.sleep(1)
            driver.execute_script("document.getElementsByName('password')[0].value=arguments[0]", pwd)
            time.sleep(1)
            break
            
        except Exception:
            if attempt == MAX_RETRIES:
                raise
            continue

    # 로그인 버튼 클릭
    driver.find_element('xpath', '//*[@id="loginBtn"]').click() # 버튼 클릭
    try:
        # 다음에 변경하기
        driver.find_element('xpath', '//*[@id="btn-extend"]').click() # 버튼 클릭
    except:
        pass
    time.sleep(3)
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
    time.sleep(5)
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
    print("5 - 인벤 출석 체크 완료")

    return f'{info1} / {info2}'

async def item_mania(driver, id, pwd):
    
    login_url = 'https://www.itemmania.com/portal/user/p_login_form.html'
    event = 'https://www.itemmania.com/event/event_ing/e190417_attend/'
    # URL the site's "add to favorites" button saves; sets the counterIDX=dot_bookmark_com cookie
    bookmark = 'https://www.itemmania.com/counter/survey.php?imcounter=dot_bookmark_com&returnUrl=https%3A%2F%2Fwww.itemmania.com'
                                                                                                                                                                                                                                                                                                                                  
    driver.implicitly_wait(10)

    # must run before login so the session counts as a favorites visit
    driver.get(bookmark)
    time.sleep(3)

    for attempt in range(MAX_RETRIES + 1):
        try:
            driver.get(login_url)
            time.sleep(5)
            login = driver.find_element('id', 'user_id')
            login.send_keys(id)
            time.sleep(1)
            login = driver.find_element('id', 'user_password')
            login.send_keys(pwd)
            time.sleep(1)
            driver.find_element('xpath', '/html/body/div[2]/main/div[2]/div[2]/form[1]/ul/li[4]/button').click()
            time.sleep(5)
            break
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise
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
    dailyCheckBtn = '/html/body/div[2]/main/div/div[3]/div/div[3]'
    driver.find_element('xpath', dailyCheckBtn).click()
    
    # 출석 됐는지 체크
    time.sleep(3)
    check = ""
    try:
        check = driver.find_element('xpath', dailyCheckBtn).text
    except:
        logger.info('아이템매니아 결과 파싱 실패 - 한번 더 시도')
        driver.refresh()
        time.sleep(3)
        check = driver.find_element('xpath', dailyCheckBtn).text

    logger.info(check)
    return check

# (personal.json key, site function) in run order
SITES = [
    ("ondisk", login_ondisk),
    ("yesfile", login_yesfile),
    ("filebogo", login_filebogo),
    ("inven", inven),
    ("inven2", inven),
    ("item_mania", item_mania),
    ("item_mania2", item_mania),
]

def take_screenshot(driver):
    """PNG bytes of the current page, or None if the browser cannot provide one."""
    # an open alert blocks screenshots
    try:
        Alert(driver).dismiss()
    except Exception:
        pass
    try:
        return driver.get_screenshot_as_png()
    except Exception:
        return None

async def run_site(driver, mode, func, account):
    """Run one site and return its result; OK only means the flow finished without an exception."""
    result = {"mode": mode, "ok": False, "detail": "", "seconds": 0, "screenshot": None}
    started = time.monotonic()
    try:
        detail = await func(driver, account[mode]["id"], account[mode]["pwd"])
        result["ok"] = True
        result["detail"] = clean(detail or "")
        logger.info(f"success {mode}")
    except Exception as e:
        result["detail"] = describe_error(e)
        # capture before the next site navigates away
        result["screenshot"] = take_screenshot(driver)
        logger.info(f"{e} - fail {mode}")
    result["seconds"] = time.monotonic() - started
    return result

async def main():
    started_at = datetime.datetime.now()
    started = time.monotonic()
    results = []
    fatal = ""
    driver = None

    try:
        account = common.open_json(".//", "personal.json")
        try:
            driver = open_driver()
        except FileNotFoundError as e:
            logger.info(f"{e} - check path : C:\\Program Files\\Google\\Chrome\\Application")
            raise

        for mode, func in SITES:
            results.append(await run_site(driver, mode, func, account))
    except Exception as e:
        fatal = describe_error(e)
        logger.error(traceback.format_exc())
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception as e:
                logger.info(f"{e} - fail driver.quit")
        await send_report(started_at, time.monotonic() - started, results, fatal)

if __name__ == "__main__":
    asyncio.run(main())
    