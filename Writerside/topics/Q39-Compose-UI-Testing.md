# Q39) Compose UI 단위 테스트

## Compose UI 컴포넌트와 화면의 단위 테스트는 어떻게 작성하나요? {#how-to-write-ui-tests}

Jetpack Compose UI 컴포넌트를 테스트하면 UI 정확성, 안정성, 사용성을 함께 보장할 수 있습니다. Compose는 UI 테스트를 효율적으로 작성하기 위한 [전용 테스트 라이브러리](https://developer.android.com/develop/ui/compose/testing)를 제공합니다. 이 라이브러리들은 Jetpack의 **ComposeTestRule** 위에 구축되어 있으며, UI 상호작용·동기화·검증 API를 함께 제공합니다.

### Compose UI 테스트 셋업 {#setting-up}

Compose 테스트는 **AndroidJUnit4** 와 **ComposeTestRule** 을 사용해 작성합니다. ComposeTestRule 이 테스트 환경 역할을 하며, UI 와의 상호작용과 테스트 액션·리컴포지션 사이의 동기화를 보장해 줍니다.

```kotlin
@get:Rule
val composeTestRule = createComposeRule()

@Test
fun verifyTextDisplayed() {
    composeTestRule.setContent {
        Text("Hello, skydoves!")
    }

    composeTestRule
        .onNodeWithText("Hello, skydoves!")
        .assertExists()
}
```
{title="VerifyTextDisplayed.kt"}

`setContent` 가 테스트 대상 UI를 초기화하고, `onNodeWithText` 가 텍스트가 일치하는 컴포저블을 찾아 그 존재를 검증합니다.

### UI 상호작용 테스트 {#testing-ui-interactions}

Compose는 버튼 클릭, 텍스트 입력, 스크롤 같은 사용자 액션을 시뮬레이션할 수 있는 API를 제공합니다.

```kotlin
@Test
fun clickButtonUpdatesText() {
    composeTestRule.setContent {
        var text by remember { mutableStateOf("Hello, skydoves!") }
        Column {
            Text(text)
            Button(onClick = { text = "Hello, Kotlin!" }) {
                Text("Click me")
            }
        }
    }

    composeTestRule.onNodeWithText("Click me").performClick()
    composeTestRule.onNodeWithText("Hello, Kotlin!").assertExists()
}
```
{title="ClickButtonUpdatesText.kt"}

`performClick()` 이 버튼 클릭을 시뮬레이션해 텍스트가 갱신되도록 만들고, `assertExists()` 로 갱신된 텍스트의 존재를 확인합니다.

### 동기화와 Idling Resources {#synchronization}

Jetpack Compose UI 테스트는 단일 스레드에서 동작하기 때문에, Compose는 **Idling Resources** 를 통해 테스트 동기화를 보장합니다. 다만 코루틴이나 애니메이션을 테스트할 때는 명시적인 동기화가 필요할 수 있습니다.

```kotlin
@Test
fun testLoadingState() {
    composeTestRule.setContent {
        var isLoading by remember { mutableStateOf(true) }
        LaunchedEffect(Unit) {
            delay(2000)
            isLoading = false
        }

        if (isLoading) {
            CircularProgressIndicator()
        } else {
            Text("Loaded")
        }
    }

    composeTestRule.waitUntilExactlyOneExists(hasText("Loaded"), 3000)
}
```
{title="TestLoadingState.kt"}

`waitUntilExactlyOneExists` 가 로딩 상태가 끝나고 "Loaded" 텍스트가 등장할 때까지 기다린 뒤 검증합니다. 다음과 같은 다양한 `waitUntil` 헬퍼도 제공됩니다.

```kotlin
composeTestRule.waitUntilAtLeastOneExists(matcher, timeoutMs)
composeTestRule.waitUntilDoesNotExist(matcher, timeoutMs)
composeTestRule.waitUntilExactlyOneExists(matcher, timeoutMs)
composeTestRule.waitUntilNodeCount(matcher, count, timeoutMs)
```
{title="WaitUntilHelpers.kt"}

코루틴·상태 변화에 따른 비동기 결과를 기다리는 패턴을 더 깊이 보고 싶다면 *Alternatives to Idling Resources in Compose tests: The waitUntil APIs* 글을 참고할 수 있습니다.

### Lazy 리스트 테스트 {#testing-lazy-lists}

`LazyColumn` 같은 스크롤 가능한 콘텐츠는 `assertIsDisplayed()` 가 항목이 뷰포트 안에 있는지 검증하고, `performScrollToNode()` 가 화면 밖 항목까지 스크롤해 테스트할 수 있게 해 줍니다.

```kotlin
@Test
fun scrollToItem() {
    val list = List(100) { "item $it" }

    composeTestRule.setContent {
        LazyColumn(modifier = Modifier.testTag("lazyColumn")) {
            items(items = list) { value ->
                Text(value, Modifier.testTag(value))
            }
        }
    }

    composeTestRule.onNodeWithTag("item50").assertDoesNotExist()
    composeTestRule.onNodeWithTag("lazyColumn").performScrollToNode(hasText("item50"))
    composeTestRule.onNodeWithTag("item50").assertIsDisplayed()
}
```
{title="ScrollToItem.kt"}

처음에는 보이지 않던 항목이 스크롤 이후 노출되는지를 검증하는 패턴입니다.

### UI Semantics와 접근성 검증 {#verifying-semantics}

Compose 테스트 프레임워크는 **시맨틱 프로퍼티(semantics properties)** 를 지원해 contentDescription 같은 접근성 속성도 검증할 수 있습니다.

```kotlin
@Test
fun testContentDescription() {
    composeTestRule.setContent {
        Icon(imageVector = Icons.Default.Home, contentDescription = "Home Icon")
    }

    composeTestRule.onNodeWithContentDescription("Home Icon").assertExists()
}
```
{title="TestContentDescription.kt"}

`onNodeWithContentDescription` 으로 접근성 라벨이 제대로 부여되었는지를 검증할 수 있습니다.

Jetpack Compose의 UI 테스트는 XML 기반 레이아웃 시절보다 훨씬 작성하기 쉬워졌습니다. 노드 쿼리, UI 상호작용, idleness 동기화에 대한 효율적인 라이브러리들이 제공되기 때문입니다. 빈번하게 활용하는 API의 한눈 정리는 [Jetpack Compose Testing Cheat Sheet](https://developer.android.com/develop/ui/compose/testing/testing-cheatsheet)에서 확인할 수 있습니다.

### 요약 {#summary}

<tldr>

Compose UI 테스트는 정확성·안정성·접근성을 함께 검증하는 도구입니다. `ComposeTestRule` 로 UI 상호작용을 시뮬레이션하고, 동기화 메커니즘으로 비동기 상태 변화를 기다리며, lazy 리스트와 시맨틱 프로퍼티까지 검증할 수 있습니다. 테스트 구조를 잘 잡아 두면 다양한 상태와 구성에서 Compose 앱이 안정적으로 동작하도록 만들 수 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 컴포저블이 올바른 UI 요소를 표시하는지를 검증하는 단위 테스트는 어떻게 작성하시겠습니까?">

가장 단순한 형태는 본문 예시처럼 `composeTestRule.setContent { ... }` 로 검증 대상 컴포저블을 띄우고, 적절한 finder API 로 노드를 찾은 뒤 `assertExists()` 로 존재 여부를 검증하는 흐름입니다. 텍스트 기반이면 `onNodeWithText("...")`, 아이콘처럼 시각적 요소면 `onNodeWithContentDescription("...")`, 디자인 시스템 컴포넌트라면 `Modifier.testTag("...")` 와 짝을 이루는 `onNodeWithTag("...")` 가 가장 자주 쓰이는 조합입니다. 한 화면을 다룰 때는 `setContent` 안에 화면 컴포저블을 통째로 넣고, 그 화면이 보여 줘야 하는 핵심 요소만 검증하는 식으로 시작하면 됩니다.

조금 더 풍부한 검증으로 넘어가면 **상태별 분기** 가 핵심이 됩니다. 같은 컴포저블이 로딩/성공/에러 상태에서 다른 UI를 보여 준다면, 각 상태를 인자로 주입할 수 있도록 컴포저블을 분리하고 상태별로 별도의 테스트 함수를 작성합니다. 이 패턴이 깔끔해지려면 화면을 "상태 객체를 받아 UI를 그리는 stateless 컴포저블" 형태로 두는 것이 좋습니다. ViewModel 까지 포함된 전체 화면 테스트는 통합 테스트 영역에 가까우므로, 단위 테스트는 stateless 컴포저블 단위로 구성하는 편이 회귀 잡기에 더 좋습니다.

마지막으로 화면이 비동기 상태를 다루는 경우(예: 데이터 로딩, 애니메이션) 에는 `waitUntilExactlyOneExists`, `waitUntilAtLeastOneExists` 같은 helper 와 함께 적절한 timeout 을 지정합니다. 이 helper 들은 idling 동기화가 자동으로 잡지 못하는 비동기 상태 전이를 안정적으로 기다려 주므로, flaky 테스트를 줄이는 데 큰 도움이 됩니다. 정리하면 "stateless 컴포저블 + 적절한 finder API + 비동기 상태에는 waitUntil*" 의 조합이 Compose 단위 테스트의 가장 단단한 토대가 됩니다.

</def>
<def title="Q) performClick()으로 사용자 액션을 시뮬레이션하고 assertExists() 또는 assertTextEquals() 같은 검증으로 결과를 확인하는 흐름을 설명해 주세요.">

흐름은 보통 세 단계로 구성됩니다. 첫째, `setContent` 안에 검증 대상 UI를 띄웁니다. 이 단계에서 화면이 가지는 초기 상태(예: 카운터 0, 비어 있는 입력 필드)를 명시적으로 만들어 두면 이후 검증의 출발점이 분명해집니다. 둘째, 사용자 액션을 흉내냅니다. 클릭은 `onNodeWithText("Click me").performClick()`, 텍스트 입력은 `onNodeWithTag("input").performTextInput("hello")`, 스크롤은 `onNodeWithTag("list").performScrollToNode(hasText("item50"))` 같은 식입니다. 셋째, 변화한 상태의 결과를 검증합니다. 새 텍스트가 등장했는지는 `assertExists()` 로, 특정 노드의 텍스트 정확도는 `assertTextEquals("기대값")` 로 확인할 수 있습니다.

세 단계 사이에는 자연스럽게 **Compose 의 동기화** 가 끼어듭니다. `performClick()` 같은 액션은 내부적으로 다음 측정·배치·드로잉이 끝날 때까지 기다린 뒤 다음 코드를 실행하므로, 클릭 직후의 `assertExists()` 가 안정적으로 갱신된 화면을 검증할 수 있습니다. 다만 액션이 코루틴이나 애니메이션과 결합된 경우에는 동기화가 자동으로 이뤄지지 않을 수 있는데, 이때 `waitUntilExactlyOneExists` 같은 helper 와 적절한 timeout 을 추가해 비동기 상태 전이를 안정적으로 기다리는 패턴이 정석입니다.

마지막으로 검증 API 도 구분해서 활용하면 의도가 더 잘 드러납니다. `assertExists()` 는 "그 노드가 화면 트리에 존재하는가" 를 묻고, `assertIsDisplayed()` 는 "현재 뷰포트에 보이는가" 까지 검증하며, `assertTextEquals("...")` 는 노드의 텍스트가 기대값과 정확히 일치하는지를 검증합니다. 이 셋을 상황에 맞게 사용하면 "보이는가/존재만 하는가/내용까지 정확한가" 가 분명한 단위 테스트로 정리되고, 회귀가 발생했을 때 어느 단계에서 깨졌는지를 단번에 짚어내기 쉬워집니다.

</def>
</deflist>
