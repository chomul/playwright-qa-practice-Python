import os
import re
import uuid
import pytest
from playwright.sync_api import Page, expect

BASE = "https://automationexercise.com"

LOGIN_EMAIL = os.environ["TEST_EMAIL"]
LOGIN_PASSWORD = os.environ["TEST_PASSWORD"]


# ── 공통 도우미 함수 ──────────────────────────────────────
def clear_cart(page: Page):
    """장바구니를 비워서 이전 실행의 영향 제거"""
    page.goto(f"{BASE}/view_cart")
    delete_buttons = page.locator("a.cart_quantity_delete")
    while delete_buttons.count() > 0:
        before = delete_buttons.count()
        delete_buttons.first.click()
        expect(delete_buttons).to_have_count(before - 1)  # 삭제될 때까지 기다림


def add_product_to_cart(page: Page, quantity: str = "1"):
    """결제 테스트에서도 재사용할 수 있게 함수로 분리"""
    page.goto(f"{BASE}/product_details/28")
    page.fill("#quantity", quantity)
    page.click("button.cart")
    page.click("a[href='/view_cart']")


# ── 공통 fixture ──────────────────────────────────────────
@pytest.fixture
def logged_in_page(page: Page):
    page.goto(f"{BASE}/login")
    page.fill("input[data-qa='login-email']", LOGIN_EMAIL)
    page.fill("input[data-qa='login-password']", LOGIN_PASSWORD)
    page.click("button[data-qa='login-button']")
    expect(page.get_by_text("Logged in as")).to_be_visible()  # 확실한 로그인 확인
    clear_cart(page)  # 항상 빈 장바구니로 시작
    return page


# ── 시나리오 1: 회원가입 ───────────────────────────────────
def test_signup(page: Page):
    # 실행할 때마다 새 이메일 → 항상 신규 가입 가능
    email = f"qa_{uuid.uuid4().hex[:8]}@test.com"

    page.goto(f"{BASE}/signup")
    page.fill("input[data-qa='signup-name']", "Test User")
    page.fill("input[data-qa='signup-email']", email)
    page.click("button[data-qa='signup-button']")
    expect(page).to_have_url(re.compile(r".*/signup"))

    page.click("#id_gender1")
    page.fill("input[data-qa='password']", "Test1234!")
    page.select_option("select[data-qa='days']", "1")
    page.select_option("select[data-qa='months']", "1")
    page.select_option("select[data-qa='years']", "2000")
    page.fill("input[data-qa='first_name']", "Test")
    page.fill("input[data-qa='last_name']", "User")
    page.fill("input[data-qa='company']", "Test Company")
    page.fill("input[data-qa='address']", "123 Test St")
    page.fill("input[data-qa='address2']", "Suite 100")
    page.select_option("select[data-qa='country']", "United States")
    page.fill("input[data-qa='state']", "Test State")
    page.fill("input[data-qa='city']", "Test City")
    page.fill("input[data-qa='zipcode']", "12345")
    page.fill("input[data-qa='mobile_number']", "1234567890")
    page.click("button[data-qa='create-account']")

    expect(page.locator("h2[data-qa='account-created']")).to_be_visible()

    # [변경] 만든 계정 삭제 → 테스트 계정이 계속 쌓이지 않음
    page.click("a[data-qa='continue-button']")
    page.click("a[href='/delete_account']")
    expect(page.locator("h2[data-qa='account-deleted']")).to_be_visible()


# ── 시나리오 2: 상품 검색 → 장바구니 추가 → 수량 확인 ────────
def test_search_and_add_to_cart(logged_in_page: Page):
    """
    상품을 검색하고 장바구니에 담는 시나리오
    - 키워드로 상품 검색
    - 첫 번째 상품 상세 페이지 진입
    - 수량 변경 후 장바구니 추가
    - 장바구니에서 수량 확인
    """

    page = logged_in_page

    # 상품 검색
    page.goto(f"{BASE}/products")
    page.fill("#search_product", "t-shirt")
    page.click("#submit_search")

    # 검색 결과에서 첫 번째 상품 클릭
    # 틀린 방식 page.locator(".features_items .product-image-wrapper").first.click()
    page.click("a[href='/product_details/28']")
    expect(page).to_have_url(re.compile(r".*/product_details/.*"))

    # 수량 변경 (2개)
    page.fill("#quantity", "2")

    # 장바구니 추가
    page.click("button.cart")
    page.click("a[href='/view_cart']")

    # 장바구니에서 수량 확인
    expect(page.locator("td.cart_quantity").first).to_have_text("2")


# ── 시나리오 3: 결제 플로우 (카드 입력까지) ──────────────────
def test_checkout_flow(logged_in_page: Page):
    """
    장바구니 → 주문서 확인 → 카드 결제 시나리오
    - 상품을 장바구니에 추가
    - 장바구니 → 체크아웃
    - 배송지 확인
    - 카드 정보 입력 후 주문 완료
    """

    page = logged_in_page
    add_product_to_cart(page)

    page.click("a.check_out")
    expect(page).to_have_url(re.compile(r".*/checkout"))

    page.fill("textarea[name='message']", "Please deliver between 9am-5pm.")
    page.click("a[href='/payment']")
    expect(page).to_have_url(re.compile(r".*/payment"))

    page.fill("input[name='name_on_card']", "Test User")
    page.fill("input[name='card_number']", "4111111111111111")
    page.fill("input[name='cvc']", "123")
    page.fill("input[name='expiry_month']", "12")
    page.fill("input[name='expiry_year']", "2025")
    page.click("#submit")

    expect(page.locator("h2[data-qa='order-placed']")).to_be_visible()
    page.screenshot(path="order_complete.png")
