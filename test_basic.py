from playwright.sync_api import Page, expect
import re


def test_title(page: Page):
    page.goto("https://playwright.dev")  # 브라우저가 해당 URL로 이동
    assert "Playwright" in page.title()  # 페이지 제목에 "Playwright"가 있는지 확인


def test_interaction(page: Page):
    page.goto("https://playwright.dev")

    # 1. 요소 클릭
    page.click("text=Get started")

    # 2. 현재 URL 확인
    assert "intro" in page.url

    # 3. 특정 텍스트가 화면에 있는지 확인
    assert page.locator("h1").is_visible()


def test_naver_search(page: Page):
    page.goto("https://www.naver.com")

    # 검색창에 텍스트 입력
    page.fill("#query", "playwright 자동화")

    # 엔터키 입력
    page.keyboard.press("Enter")

    # 검색 결과 페이지로 이동했는지 확인
    page.wait_for_load_state("load")
    expect(page).to_have_url(re.compile(r".*search\.naver\.com.*"))


def test_screenshot(page: Page):
    page.goto("https://www.naver.com")

    # 전체 페이지 스크린샷
    page.screenshot(path="naver_full.png", full_page=True)

    # 특정 요소만 스크린샷
    page.locator("#shortcutArea").screenshot(path="naver_menu.png")


def test_naver_interaction(page: Page):
    context = page.context
    menus = [
        ("웹툰", ".*comic\.naver\.com.*"),
        ("뉴스", ".*news\.naver\.com.*"),
        ("치지직", ".*chzzk\.naver\.com.*"),
    ]

    for pagename, url_pattern in menus:
        page.goto("https://www.naver.com")

        # [수정 1] 영역을 확실히 제한합니다 (상단 메뉴 영역만 검색)
        # 네이버 상단 메뉴 아이디는 보통 'shortcutArea'입니다.
        locator = page.locator("#shortcutArea").get_by_role("link", name=pagename)

        # 만약 그래도 여러 개가 잡힌다면 .first를 붙여 첫 번째 것을 선택합니다.
        target_link = locator.first

        try:
            # [수정 2] 새 탭 대기
            with context.expect_page(timeout=5000) as new_page_info:
                target_link.click()

            # 새 탭 처리
            new_page = new_page_info.value
            expect(new_page).to_have_url(re.compile(url_pattern))
            new_page.close()

        except Exception as e:
            # 만약 타임아웃(새 탭 안뜸) 에러라면 현재 페이지 URL 확인
            if "Timeout" in str(e):
                expect(page).to_have_url(re.compile(url_pattern))
            else:
                # 클릭 자체를 못 한 다른 에러라면 테스트 실패 처리
                raise e
