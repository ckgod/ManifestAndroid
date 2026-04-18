# Q10) Jetpack Compose에서 자주 쓰이는 Kotlin Idiom

## Jetpack Compose는 어떤 Kotlin idiom을 자주 사용하나요? {#kotlin-idioms-in-compose}

Jetpack Compose는 Kotlin과 깊이 통합되어 있고, Kotlin의 강력한 언어 기능을 활용해 더 표현력 있고 효율적인 UI 개발 경험을 제공합니다. Kotlin idiom 들을 이해하고 있으면 짧고 읽기 좋은 Compose 코드를 자연스럽게 작성할 수 있습니다.

### 기본 인자(Default Arguments) {#default-arguments}

Kotlin은 함수 파라미터에 기본값을 지정할 수 있어 함수 오버로드의 부담을 크게 줄여 줍니다. Compose는 이 특성을 적극 활용해 API 사용을 간결하게 만듭니다. 예를 들어 `Text` 컴포저블은 다양한 옵션 파라미터에 기본값을 두어 최소한의 호출로도 동작하도록 설계되어 있습니다. 이름 있는 인자(named arguments)와 결합하면 가독성이 한층 좋아집니다.

```kotlin
Text("Hello, Android!")
// 다음과 동일합니다.
Text(
    text = "Hello, Android!",
    color = Color.Unspecified,
    fontSize = TextUnit.Unspecified
)
```
{title="DefaultArgumentsExample.kt"}

코드의 유지보수성과 명료함이 함께 올라갑니다.

### 고차 함수와 람다 표현식 {#higher-order-functions}

Compose는 다른 함수를 파라미터로 받는 고차 함수(higher-order functions)를 광범위하게 사용합니다. `Button` 처럼 사용자 상호작용을 다루는 컴포넌트의 `onClick` 람다가 대표적인 예입니다.

```kotlin
Button(onClick = { showToast("Clicked!") }) {
    Text("Click Me")
}
```
{title="HigherOrderFunctionExample.kt"}

별도의 함수를 정의하는 대신 동작을 인라인 람다로 적어 두면, 코드 흐름이 자연스러워지고 의도도 더 잘 드러납니다.

### 후행 람다(Trailing Lambdas) {#trailing-lambdas}

마지막 파라미터로 람다를 받는 함수의 경우, 그 람다를 괄호 밖에 둘 수 있는 Kotlin의 특별한 문법이 적용됩니다. `Column` 같은 Compose 레이아웃 함수에서 자주 보입니다.

```kotlin
Column {
    Text("Item 1")
    Text("Item 2")
}
```
{title="TrailingLambdaExample.kt"}

이 한 가지 문법 덕분에 Compose의 레이아웃 코드는 트리 구조를 그대로 글로 옮긴 것처럼 보입니다.

### 스코프와 리시버(Scopes & Receivers) {#scopes-receivers}

Compose API는 특정 컨텍스트 안에서만 접근 가능한 modifier 나 프로퍼티를 노출하기 위해 스코프 기반 함수를 자주 사용합니다. 예를 들어 `RowScope` 안에서는 행 정렬에 한정된 옵션을 사용할 수 있습니다.

```kotlin
Row {
    Text(
        text = "Hello",
        modifier = Modifier.align(Alignment.CenterVertically)
    )
}
```
{title="ScopesAndReceiversExample.kt"}

이 패턴 덕분에 코드 조직이 깔끔해지고, 의도한 컨텍스트 밖에서 함수가 잘못 사용되는 일도 자연스럽게 막을 수 있습니다.

### 위임 프로퍼티(Delegated Properties) {#delegated-properties}

Compose는 상태를 효율적으로 다루기 위해 `by` 문법으로 표현되는 위임 프로퍼티를 적극 활용합니다. `remember` 가 리컴포지션을 가로질러 값을 보존하고, `mutableStateOf` 가 UI를 반응형으로 만들어 줍니다.

```kotlin
var count by remember { mutableStateOf(0) }
```
{title="DelegatedPropertiesExample.kt"}

값이 바뀌면 자동으로 리컴포지션이 트리거되므로 상태 관리 코드가 단순해집니다.

### Data Class 구조 분해 {#destructuring}

Kotlin의 구조 분해(destructuring) 기능은 특히 ConstraintLayout처럼 제약 기반 레이아웃을 다룰 때 유용합니다.

```kotlin
val (image, title, subtitle) = createRefs()
```
{title="DestructuringExample.kt"}

코드의 의도가 더 분명해지고 불필요한 변수 선언도 줄어듭니다.

### 싱글톤 객체 {#singleton-objects}

Kotlin의 `object` 선언은 싱글톤 생성을 단순하게 만들어 줍니다. `MaterialTheme` 같은 테마 시스템에서 흔히 볼 수 있습니다.

```kotlin
val primaryColor = MaterialTheme.colorScheme.primary
```
{title="SingletonObjectExample.kt"}

앱 전반에 걸쳐 일관된 스타일을 보장하는 데 자연스럽게 어울립니다.

### 타입 안전 빌더와 DSL {#type-safe-builders-dsl}

Jetpack Compose는 Kotlin DSL 기능을 활용해 선언형 UI 구조를 만들어 냅니다. 예를 들어 `LazyColumn` 은 타입 안전 빌더로 계층적 UI 요소를 가독성 좋게 표현합니다.

```kotlin
LazyColumn {
    item { Text("Header") }
    items(listOf("Item 1", "Item 2")) { Text(it) }
}
```
{title="TypeSafeBuildersExample.kt"}

짧은 코드로 구조화된 UI 정의가 가능해집니다.

### Kotlin Coroutines {#coroutines}

Compose는 코루틴과 매끄럽게 통합되어 비동기 작업을 효율적으로 다룰 수 있게 해 줍니다. `rememberCoroutineScope` 는 리컴포지션을 가로질러 살아남는 코루틴 스코프를 제공합니다.

```kotlin
val scope = rememberCoroutineScope()

Button(onClick = {
    scope.launch {
        scrollState.animateScrollTo(0)
    }
}) {
    Text("Scroll to Top")
}
```
{title="CoroutinesExample.kt"}

코루틴 덕분에 콜백 중심의 코드를 걷어내고 비동기 흐름을 더 간결하게 표현할 수 있습니다.

### 요약 {#summary}

<tldr>

Compose는 Kotlin idiom 들을 적극적으로 받아들여 더 직관적이고 표현력 있는 UI 개발 경험을 제공합니다. 기본 인자, 람다 표현식, 후행 람다, DSL 같은 기능은 가독성을 끌어올리고, 위임 프로퍼티와 코루틴은 상태 관리와 비동기 처리의 비용을 줄여 줍니다. 이 Kotlin 기능들을 잘 이해하고 사용하면 Compose 코드가 짧고 명료하면서도 효율적이고 유지보수하기 좋은 형태로 자리 잡습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 후행 람다(trailing lambda)와 고차 함수(higher-order function)는 컴포저블을 구성하는 데 어떤 역할을 하나요?">

후행 람다와 고차 함수는 Compose가 "UI 트리를 코드 구조 자체로 표현" 할 수 있게 만들어 주는 두 축입니다. Compose의 레이아웃 컴포저블들은 보통 마지막 파라미터로 `content: @Composable () -> Unit` 같은 람다를 받는데, 후행 람다 문법 덕분에 이 람다를 괄호 밖에 그대로 둘 수 있습니다. 결과적으로 `Column { Text("A") Text("B") }` 처럼 부모 → 자식 관계가 코드 들여쓰기에 그대로 반영되고, XML 트리를 한 줄짜리 함수 호출로 옮긴 것처럼 자연스러운 모양이 됩니다.

여기에 더해 컴포저블 람다는 단순한 콜백이 아니라 **수신자 타입을 가진 람다(receiver lambda)** 인 경우가 많습니다. 예를 들어 `Row` 의 `content` 는 `RowScope` 를 수신자로 받기 때문에, 람다 본문 안에서는 `Modifier.align(...)` 같은 행 전용 API에 접근할 수 있습니다. 이런 식으로 고차 함수의 시그니처가 곧 "이 자리에서 어떤 컴포저블이 어떤 컨텍스트로 호출되어야 하는가" 를 타입으로 강제하는 역할을 합니다. 그 결과 의도하지 않은 위치에 잘못된 modifier를 붙이려 하면 컴파일러가 그 자리를 막아 줍니다.

그래서 사용자 정의 컴포저블을 만들 때도 두 idiom 을 함께 활용하는 패턴이 정착되어 있습니다. 재사용 컴포저블은 마지막 파라미터로 `content: @Composable RowScope.() -> Unit` 같은 수신자 람다를 노출해 두고, 호출 측에서는 후행 람다 문법으로 그 안에 자식들을 늘어놓도록 하는 식입니다. 이렇게 작성된 컴포저블은 호출 코드가 짧아지면서도 컨텍스트 안전성이 유지되고, Compose가 추구하는 "UI는 함수의 호출 트리" 라는 모델에 자연스럽게 녹아듭니다.

</def>
</deflist>
