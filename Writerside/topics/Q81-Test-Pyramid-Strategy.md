# Q81) 테스트 피라미드와 전략

## 테스트 피라미드란 {#pyramid-intro}

테스트 피라미드(test pyramid)는 자동화 테스트를 **실행 속도와 격리 수준**에 따라 계층으로 나누고, 각 계층에 **얼마나 많은 테스트를 둘지 비중을 정하는** 지침입니다. Mike Cohn이 제안한 모델로, 아래로 갈수록 빠르고 많은 테스트, 위로 갈수록 느리고 적은 테스트를 둡니다.

안드로이드에서는 보통 세 계층으로 나눕니다.

| 계층 | 무엇을 검증하나 | 실행 환경 | 속도 | 권장 비중 |
|------|----------------|-----------|------|-----------|
| 단위(Unit) | 클래스/함수 하나의 로직 | JVM (로컬) | 매우 빠름 | 많음 (~70%) |
| 통합(Integration) | 여러 컴포넌트의 상호작용 | JVM 또는 Robolectric | 중간 | 중간 (~20%) |
| UI(End-to-End) | 화면·사용자 흐름 | 실기기/에뮬레이터 | 느림 | 적음 (~10%) |

비중은 절대적인 수치가 아니라 **개수의 분포**를 가리킵니다. 핵심은 "빠르고 안정적인 테스트를 다수, 느리고 깨지기 쉬운 테스트를 소수"라는 형태입니다.

## 단위·통합·UI 비중 {#layer-ratio}

세 계층의 비중을 피라미드 형태로 두는 데에는 **명확한 비용·신뢰도 트레이드오프**가 있습니다.

### 단위 테스트: 넓은 바닥 {#unit-layer}

단위 테스트는 의존성을 가짜로 대체한 채 **클래스 하나의 로직만** 검증합니다. 안드로이드 프레임워크에 의존하지 않으므로 순수 JVM(`src/test/`)에서 실행되어 수 밀리초 단위로 끝납니다.

```kotlin
class PriceCalculatorTest {
    private val calculator = PriceCalculator()

    @Test
    fun `10퍼센트 할인을 적용한다`() {
        val result = calculator.applyDiscount(price = 1000, rate = 0.1)
        assertEquals(900, result)
    }
}
```

바닥을 넓게 가져가는 이유는 **빠르고, 실패 원인이 좁기** 때문입니다. 테스트가 실패하면 거의 그 클래스 안에 버그가 있으므로 디버깅 범위가 좁습니다.

### 통합 테스트: 중간층 {#integration-layer}

통합 테스트는 **여러 컴포넌트가 함께 동작하는 경계**를 검증합니다. 예를 들어 ViewModel과 Repository, 또는 Repository와 Room DAO가 올바르게 연결되는지 봅니다. 안드로이드 컴포넌트(예: Room, SQLite)가 필요하면 `src/androidTest/`에서 계측 테스트로 돌리거나, JVM에서 Robolectric으로 프레임워크를 흉내 내 돌립니다.

```kotlin
@RunWith(AndroidJUnit4::class)
class UserDaoTest {
    private lateinit var db: AppDatabase
    private lateinit var dao: UserDao

    @Before
    fun setup() {
        db = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            AppDatabase::class.java
        ).build()
        dao = db.userDao()
    }

    @After fun teardown() = db.close()

    @Test
    fun `삽입한 유저를 다시 읽어온다`() = runTest {
        dao.insert(User(id = 1, name = "kim"))
        assertEquals("kim", dao.getById(1)?.name)
    }
}
```

단위보다 느리고 실패 원인 범위가 넓으므로 개수를 줄이되, **단위 테스트가 잡지 못하는 연결 지점**만 골라 검증합니다.

### UI 테스트: 좁은 꼭대기 {#ui-layer}

UI 테스트(End-to-End)는 실제 화면에서 **사용자 흐름 전체**를 검증합니다. Espresso(View) 또는 Compose 테스트 API로 작성하고, 에뮬레이터/실기기에서 앱을 띄워 실행합니다.

```kotlin
@RunWith(AndroidJUnit4::class)
class LoginFlowTest {
    @get:Rule val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun `로그인 성공 시 홈으로 이동한다`() {
        composeRule.onNodeWithTag("email").performTextInput("a@b.com")
        composeRule.onNodeWithTag("password").performTextInput("pw1234")
        composeRule.onNodeWithText("로그인").performClick()
        composeRule.onNodeWithText("환영합니다").assertIsDisplayed()
    }
}
```

UI 테스트를 소수로 두는 이유는 세 가지입니다.

1. **느립니다.** 앱 빌드·설치·UI 렌더링이 필요해 한 건에 수 초가 걸립니다.
2. **불안정(flaky)합니다.** 애니메이션·네트워크 지연·타이밍 때문에 같은 테스트가 통과·실패를 오갑니다.
3. **실패 원인이 넓습니다.** 화면 전체 경로 중 어디가 깨졌는지 좁히기 어렵습니다.

그래서 UI 테스트는 **핵심 사용자 시나리오(로그인, 결제 등)** 의 회귀만 막는 용도로 최소한만 둡니다.

### 안티패턴: 아이스크림 콘 {#anti-pattern}

비중이 뒤집혀 UI 테스트가 가장 많은 형태를 아이스크림 콘(ice-cream cone)이라 부릅니다. 이 경우 테스트 묶음(suite) 전체가 느려지고 flaky해져, 개발자가 결과를 신뢰하지 않고 무시하게 됩니다. 피라미드 형태를 권장하는 본질적 이유가 바로 이 신뢰성·속도의 붕괴를 막는 것입니다.

## 테스트 가능한 설계 {#testable-design}

피라미드의 바닥(단위 테스트)을 넓게 가져가려면, **코드가 단위로 테스트 가능하게 설계**되어 있어야 합니다. 테스트하기 어려운 코드는 대부분 설계 문제이며, 다음 원칙으로 풀립니다.

### 의존성 주입으로 외부를 갈아끼운다 {#dependency-injection}

객체가 자신의 의존성을 내부에서 직접 생성하면(`val repo = UserRepository()`), 테스트에서 그 의존성을 가짜로 바꿀 수 없습니다. 의존성을 **생성자 파라미터로 주입**받으면 테스트에서 가짜 구현을 넣을 수 있습니다.

```kotlin
// 나쁨 — Repository를 내부에서 생성해 교체 불가
class BadViewModel {
    private val repo = UserRepository(RealApi())   // 테스트 시 실제 네트워크를 탄다
}

// 좋음 — 주입받아 테스트에서 교체 가능
class UserViewModel(
    private val repo: UserRepository
) {
    suspend fun loadName(id: Int): String = repo.getUser(id).name
}
```

### 인터페이스로 경계를 만든다 {#interface-boundary}

주입 대상을 **인터페이스(추상)** 로 두면 테스트에서 가짜 구현(fake)을 손쉽게 끼울 수 있습니다.

```kotlin
interface UserRepository {
    suspend fun getUser(id: Int): User
}

// 테스트용 가짜 구현 — 네트워크 없이 정해진 값을 돌려준다
class FakeUserRepository : UserRepository {
    override suspend fun getUser(id: Int) = User(id, "kim")
}

@Test
fun `유저 이름을 노출한다`() = runTest {
    val vm = UserViewModel(FakeUserRepository())
    assertEquals("kim", vm.loadName(1))
}
```

### 부수효과를 한곳으로 몰고 로직을 분리한다 {#side-effect-isolation}

순수 함수(같은 입력 → 같은 출력, 부수효과 없음)는 테스트가 가장 쉽습니다. 시간, 난수, 네트워크, 디스크 같은 **부수효과를 일으키는 부분을 경계 클래스로 분리**하면, 계산 로직 자체는 순수 함수로 남아 단위 테스트가 쉬워집니다. 예를 들어 `System.currentTimeMillis()`를 직접 부르는 대신 `Clock`을 주입받으면, 테스트에서 시간을 고정할 수 있습니다.

```kotlin
class TokenValidator(private val clock: Clock) {
    fun isExpired(token: Token): Boolean =
        token.expiresAt.isBefore(clock.instant())
}

// 테스트에서 시간을 고정
val fixed = Clock.fixed(Instant.parse("2026-01-01T00:00:00Z"), ZoneOffset.UTC)
```

### 정적 호출과 안드로이드 컨텍스트 의존을 줄인다 {#static-android-deps}

`Log`, `Toast`, 싱글톤 정적 메서드, `Context` 직접 참조 등은 JVM 단위 테스트에서 호출되지 않거나 예외를 던집니다. 이런 의존을 로직에서 떼어내고 ViewModel/도메인 계층은 안드로이드 타입에 의존하지 않게 하면, 그 계층 전체가 순수 JVM에서 빠르게 테스트됩니다. **"테스트하기 어렵다"는 신호는 곧 설계를 분리하라는 신호**입니다.

## FIRST 원칙 {#first-principles}

FIRST는 **좋은 단위 테스트가 갖춰야 할 다섯 속성**의 머리글자입니다. Robert C. Martin이 정리한 기준으로, 특히 피라미드 바닥의 단위 테스트가 신뢰받으려면 이 속성들을 만족해야 합니다.

### Fast — 빠를 것 {#first-fast}

단위 테스트는 수 밀리초 안에 끝나야 합니다. 느리면 개발자가 자주 돌리지 않게 되고, 그 순간 테스트의 피드백 가치가 사라집니다. 그래서 단위 테스트에서는 실제 네트워크·DB·`Thread.sleep` 같은 느린 의존을 가짜로 대체합니다.

### Independent — 독립적일 것 {#first-independent}

각 테스트는 다른 테스트의 실행 순서나 상태에 의존하지 않아야 합니다. 테스트 A가 만든 전역 상태를 테스트 B가 읽으면, 순서가 바뀌거나 일부만 돌릴 때 실패합니다. 공유 상태는 `@Before`에서 매번 초기화해 격리합니다.

### Repeatable — 반복 가능할 것 {#first-repeatable}

언제 어디서 돌려도 같은 결과가 나와야 합니다. 현재 시각, 난수, 네트워크 응답, 타임존처럼 **외부 환경에 따라 변하는 값**을 직접 쓰면 결과가 흔들립니다. 위 `Clock` 주입처럼 이런 값을 고정해 주입하면 반복 가능성이 확보됩니다.

### Self-validating — 스스로 검증할 것 {#first-self-validating}

테스트는 `assert`로 **통과/실패를 코드가 스스로 판정**해야 합니다. 로그를 찍어 사람이 눈으로 확인하는 방식은 자동화의 의미가 없습니다.

```kotlin
// 나쁨 — 사람이 로그를 봐야 한다
@Test fun bad() { println(calculator.applyDiscount(1000, 0.1)) }

// 좋음 — 코드가 판정한다
@Test fun good() { assertEquals(900, calculator.applyDiscount(1000, 0.1)) }
```

### Timely — 적시에 작성할 것 {#first-timely}

테스트는 프로덕션 코드와 가까운 시점에, 늦지 않게 작성해야 합니다. TDD에서는 구현 직전에 테스트를 먼저 쓰는 것을 뜻하며, 일반적으로는 기능을 다 만들고 한참 뒤로 미루지 말라는 의미입니다. 미룰수록 테스트하기 어려운 설계가 굳어지고, 작성 부담이 커져 결국 건너뛰게 됩니다.

## 요약 {#summary}

> **TL;DR** — 테스트 피라미드는 빠르고 격리된 단위 테스트를 다수, 느리고 깨지기 쉬운 UI 테스트를 소수로 두는 비중 지침입니다(~70/20/10). 이 형태가 가능하려면 의존성 주입·인터페이스·부수효과 분리로 코드가 단위 테스트 가능하게 설계돼야 하고, 각 단위 테스트는 FIRST(Fast·Independent·Repeatable·Self-validating·Timely)를 만족해야 신뢰받습니다.

1. **단위·통합·UI 비중**: 빠르고 실패 원인이 좁은 단위 테스트를 바닥에 다수, 느리고 flaky한 UI 테스트를 꼭대기에 소수. 비중이 뒤집히면(아이스크림 콘) suite가 느려지고 신뢰를 잃는다.
2. **테스트 가능한 설계**: 의존성 주입, 인터페이스 경계, 부수효과(시간·네트워크) 분리로 로직을 순수하게 만들어야 피라미드 바닥을 넓힐 수 있다. "테스트가 어렵다"는 곧 설계 분리 신호다.
3. **FIRST 원칙**: 좋은 단위 테스트의 다섯 속성 — Fast, Independent, Repeatable, Self-validating, Timely.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 테스트 피라미드에서 각 계층의 비중을 그렇게 두는 이유는 무엇인가요?">

피라미드는 단위 테스트를 다수(약 70%), 통합을 중간(약 20%), UI를 소수(약 10%)로 두는 비중 지침입니다. 단위 테스트는 순수 JVM에서 수 밀리초로 끝나고, 실패하면 원인이 한 클래스로 좁혀져 디버깅이 쉽습니다. 그래서 바닥을 넓게 가져갑니다.

반대로 UI 테스트는 앱을 빌드·설치하고 실기기/에뮬레이터에서 화면을 렌더링하므로 한 건에 수 초가 걸리고, 타이밍·애니메이션 때문에 flaky하며, 실패 시 화면 경로 중 어디가 깨졌는지 좁히기 어렵습니다. 비중이 뒤집혀 UI 테스트가 가장 많아지면(아이스크림 콘) 전체 suite가 느리고 불안정해져 개발자가 결과를 신뢰하지 않고 무시하게 됩니다. 피라미드 형태는 이 신뢰성·속도의 붕괴를 막기 위한 것입니다.

</def>
<def title="Q) 안드로이드에서 단위 테스트와 계측(통합/UI) 테스트는 어디서 어떻게 실행되나요?">

단위 테스트는 `src/test/`에 두고 순수 JVM에서 실행됩니다. 안드로이드 프레임워크에 의존하지 않으므로 에뮬레이터 없이 빠르게 돌고, ViewModel·도메인 로직처럼 안드로이드 타입에 의존하지 않게 설계한 계층이 여기에 해당합니다.

계측 테스트는 `src/androidTest/`에 두고 실기기/에뮬레이터에서 실행됩니다. Room, `Context`, 실제 UI처럼 안드로이드 런타임이 필요한 통합·UI 테스트가 여기 속합니다. 한편 Robolectric을 쓰면 안드로이드 프레임워크를 JVM에서 흉내 내어 일부 통합 테스트를 에뮬레이터 없이 빠르게 돌릴 수도 있습니다. 핵심은 "프레임워크 의존이 없으면 JVM에서, 있으면 계측으로"라는 구분입니다.

</def>
<def title="Q) 테스트하기 어려운 코드를 테스트 가능하게 만들려면 무엇을 바꿔야 하나요?">

테스트하기 어렵다는 것은 대부분 의존성을 교체할 수 없다는 뜻입니다. 첫째, 의존성을 클래스 내부에서 직접 생성하지 말고 생성자로 주입받게 합니다. 그러면 테스트에서 실제 네트워크·DB 대신 가짜 구현을 넣을 수 있습니다. 둘째, 주입 대상을 인터페이스로 추상화하면 가짜(fake) 구현을 손쉽게 끼울 수 있습니다.

셋째, 시간·난수·네트워크 같은 부수효과를 경계 클래스로 분리해 계산 로직을 순수 함수로 남깁니다. 예를 들어 `System.currentTimeMillis()`를 직접 부르는 대신 `Clock`을 주입받으면 테스트에서 시간을 고정할 수 있습니다. 넷째, `Log`·`Toast`·`Context` 같은 안드로이드 정적/컨텍스트 의존을 도메인·ViewModel 계층에서 떼어내면 그 계층 전체를 순수 JVM에서 빠르게 테스트할 수 있습니다.

</def>
<def title="Q) FIRST 원칙이 무엇이고 각각 무엇을 의미하나요?">

FIRST는 좋은 단위 테스트가 갖춰야 할 다섯 속성의 머리글자입니다.

Fast(빠름)는 수 밀리초 안에 끝나 자주 돌릴 수 있어야 한다는 것입니다. Independent(독립)는 테스트가 서로의 실행 순서나 상태에 의존하지 않아야 한다는 것으로, 공유 상태를 `@Before`에서 초기화해 격리합니다. Repeatable(반복 가능)은 언제 어디서 돌려도 같은 결과가 나와야 한다는 것으로, 현재 시각·난수·네트워크 같은 외부 변동 요소를 고정해 주입합니다. Self-validating(자가 검증)은 `assert`로 통과/실패를 코드가 스스로 판정해야 한다는 것입니다. Timely(적시성)는 테스트를 프로덕션 코드와 가까운 시점에 작성해 테스트하기 어려운 설계가 굳는 것을 막는다는 의미입니다.

</def>
<def title="Q) UI 테스트가 flaky한 이유는 무엇이고, 비중을 어떻게 가져가야 하나요?">

UI 테스트는 실제 앱을 띄워 화면을 렌더링하며 동작하므로, 애니메이션·네트워크 지연·렌더링 타이밍 같은 비결정적 요소에 노출됩니다. 같은 테스트가 환경에 따라 통과와 실패를 오가는 flaky 현상이 여기서 비롯됩니다. 또 빌드·설치·렌더링이 필요해 단위 테스트보다 수백 배 느립니다.

그래서 UI 테스트는 피라미드 꼭대기에 소수만 둡니다. 모든 분기를 UI로 검증하려 하지 말고, 로그인·결제처럼 핵심 사용자 시나리오의 회귀만 막는 용도로 최소화합니다. 세부 로직과 분기는 단위 테스트로, 컴포넌트 연결은 통합 테스트로 내려서 검증하는 것이 전체 suite를 빠르고 안정적으로 유지하는 방법입니다.

</def>
</deflist>
