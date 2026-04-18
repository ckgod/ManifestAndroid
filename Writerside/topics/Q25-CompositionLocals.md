# Q25) CompositionLocals

## CompositionLocals의 역할은 무엇인가요? {#role-of-compositionlocals}

[CompositionLocal](https://developer.android.com/develop/ui/compose/compositionlocal)은 컴포지션 트리를 따라 데이터를 **암묵적으로 내려보낼 수 있게** 해 주는 Jetpack Compose의 메커니즘입니다. 데이터를 모든 컴포저블 함수에 일일이 파라미터로 통과시키지 않아도 되므로, 깔끔하고 확장성 있는 UI 아키텍처를 유지하기에 좋습니다.

각 컴포저블이 공유 데이터를 받아 자식에게 다시 전달해야 한다면 코드가 빠르게 지저분해집니다. CompositionLocal을 사용하면 UI 계층의 어느 위치에서든 그 데이터를 곧바로 꺼내 쓸 수 있어, 텍스트 스타일, 색상 스킴, 내비게이션 핸들러 같은 전역 구성·테마·의존성을 다루기에 자연스럽게 어울립니다.

### CompositionLocal이 왜 필요한가 {#why-compositionlocal}

Jetpack Compose는 선언형 접근을 따르기 때문에 UI를 매우 재사용성 있고 직관적으로 만들 수 있습니다. 다만 레이아웃의 루트에서 제공한 데이터가 깊게 쌓인 컴포저블 안에서 필요해지는 순간부터 어려움이 시작됩니다. 단순한 UI 구조에서는 큰 문제가 없지만, 10단계가 넘는 중첩이 있는 복잡한 레이아웃에서는 매번 파라미터로 데이터를 흘려보내는 일이 큰 비용으로 다가옵니다.

이 문제를 해결하기 위해 Jetpack Compose는 CompositionLocal 메커니즘을 제공합니다. 컴포지션 트리 전반에 걸쳐 데이터가 암묵적으로 흐르도록 하여, 어떤 깊이에 있는 컴포저블이든 필요한 정보에 바로 접근할 수 있게 만들어 줍니다. 깊고 복잡한 UI 계층에서 필요한 데이터를 한정된 스코프 안에서 꺼내 쓰는 방식이 깔끔해집니다.

대부분의 경우 CompositionLocal은 한번 초기화되면 거의 변하지 않는 비교적 정적인 정보를 전달하는 데 사용됩니다. 대표적인 예가 `MaterialTheme` 객체이며, Compose UI 컴포넌트 전반에 걸쳐 일관된 디자인을 유지하는 역할을 합니다. 내부 구현은 다음과 같이 되어 있습니다.

```kotlin
@Composable
fun MaterialTheme(
    // ...
) {
    // ...
    CompositionLocalProvider(
        LocalColors provides rememberedColors,
        LocalContentAlpha provides ContentAlpha.high,
        LocalIndication provides rippleIndication,
        LocalRippleTheme provides MaterialRippleTheme,
        LocalShapes provides shapes,
        LocalTextSelectionColors provides selectionColors,
        LocalTypography provides typography
    ) {
        // ...
    }
}
```
{title="MaterialTheme.kt"}

### 사용 예시 {#example-usage}

여러 컴포저블에 걸쳐 사용자 객체를 공유하는 예를 통해 CompositionLocal의 사용 모습을 살펴봅니다.

```kotlin
val LocalUser = compositionLocalOf { "skydoves" }

@Composable
fun UserProfile() {
    Column {
        Text(text = "User: ${LocalUser.current}")
        UserDetails()
    }
}

@Composable
fun UserDetails() {
    Text(text = "Welcome, ${LocalUser.current}!")
}

@Composable
fun App() {
    CompositionLocalProvider(LocalUser provides "Android") {
        UserProfile()
    }
}
```
{title="CompositionLocalExample.kt"}

`LocalUser` 객체가 상위 수준(`App` 컴포저블)에서 제공되고, `UserProfile` 과 `UserDetails` 안에서는 별도의 파라미터 없이 암묵적으로 접근됩니다.

### 요약 {#summary}

<tldr>
CompositionLocal은 Compose 트리 전반에 걸쳐 데이터를 암묵적으로 공유하게 해 주는 메커니즘으로, 파라미터를 일일이 통과시킬 필요를 줄여 줍니다. 테마, 사용자 세션, 내비게이션 핸들러 같은 전역 구성을 다루는 데 특히 유용합니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) CompositionLocal 이란 무엇이며, 어떤 시나리오에서 컴포저블 함수에 파라미터를 직접 전달하는 대신 CompositionLocal 을 선택하나요?">

CompositionLocal 은 **암묵적인 의존성 주입 채널** 에 가깝습니다. 컴포지션 트리의 어느 지점에서 `CompositionLocalProvider` 로 값을 제공해 두면, 그 아래에 있는 모든 컴포저블이 별도의 파라미터 전달 없이 `Local*.current` 로 그 값을 꺼내 쓸 수 있게 됩니다. 즉 부모 → 자식 → 손자 식으로 같은 값을 계속 전달해야 하는 보일러플레이트를 제거하고, 대신 "이 영역에서는 이 값을 사용한다" 라는 컨텍스트 단위 약속으로 바꿔 주는 도구입니다.

선택 기준을 단순화하면 **"호출 트리 어디서나 같은 값으로 일관되게 동작해야 하는 환경적·컨텍스트적 정보" 인가** 입니다. 테마(`MaterialTheme.colors`), 타이포그래피, 콘텐츠 색상, 컨텍스트(`LocalContext`), 라이프사이클 오너(`LocalLifecycleOwner`), 내비게이션 컨트롤러처럼 한 화면 전체가 공유하는 정보가 대표적인 후보입니다. 이런 값을 일반 파라미터로 통과시키면 깊이가 깊어질수록 코드가 같은 값을 옮겨 적기만 하는 형태가 되고, 중간 컴포저블이 그 값을 사용하지 않으면서도 시그니처에 들고 있어야 하는 불편이 생깁니다.

반대로 **그 자리의 비즈니스 데이터(사용자 프로필, 화면별 ViewModel 상태, 현재 선택 항목 등)** 는 CompositionLocal 의 대상이 아니라 **그냥 파라미터로 흘려보내는 편이 좋습니다.** 데이터의 출처가 명시적으로 드러나야 테스트와 추적이 쉬워지고, 화면 일부분만 분리하거나 미리보기에 띄우는 경우에도 의존성이 한눈에 보입니다. CompositionLocal 은 잘못 사용하면 "이 값이 어디서 왔는지 보이지 않는" 마법 같은 의존성을 만들기 쉬우므로, 자주 바뀌고 화면별 도메인에 깊이 묶인 데이터는 가능한 한 평범한 파라미터로 두고 환경적 정보만 CompositionLocal 로 다루는 분리가 안전합니다.

</def>
<def title="Q) CompositionLocalProvider 는 어떻게 동작하며, 값이 제공되지 않은 CompositionLocal 에 접근하면 어떤 일이 일어나나요?">

`CompositionLocalProvider` 는 그 람다 본문이 컴포지션되는 동안 특정 CompositionLocal 들이 어떤 값을 갖는지 지정하는 **스코프 지정자** 입니다. `provides` 로 묶인 키-값 쌍이 람다 본문 내부 컴포지션의 일부가 되어, 그 안의 컴포저블들이 `Local*.current` 를 통해 그 값을 꺼내 쓸 수 있게 됩니다. 같은 `Local` 을 더 깊은 위치에서 다른 값으로 다시 제공하면 그 안쪽 영역에서는 새로 제공된 값이 우선합니다. 즉 가장 가까운 부모 Provider 의 값이 적용되는 **레키시컬 스코핑** 모델이라고 보면 자연스럽습니다.

값이 제공되지 않은 CompositionLocal 에 접근했을 때의 동작은 두 가지로 갈립니다. `compositionLocalOf { ... }` 로 만들 때 람다 안에서 **기본값(default value)** 을 지정해 두면, 어떤 Provider 도 만나지 못한 상태에서 `Local*.current` 가 호출되면 그 기본값이 반환됩니다. 반면 기본값이 없는 형태(예: `compositionLocalOf&lt;NavController&gt; { error("not provided") }` 처럼 명시적으로 예외를 던지도록 만든 경우)에서는 값이 제공되지 않은 채로 접근하는 순간 런타임에 예외가 발생합니다. `staticCompositionLocalOf` 도 동일한 패턴을 따라, 기본값 없이 만든다면 사용 시점에 항상 Provider 가 보장되도록 강제할 수 있습니다.

이런 동작은 두 가지 설계 선택을 뒷받침합니다. 첫째, **기본값이 의미 있는 환경 정보**(예: 기본 콘텐츠 색상, 기본 타이포그래피)는 `compositionLocalOf` 의 기본값으로 정의해 두면 어디서 호출되든 Compose 가 안전하게 동작합니다. 둘째, **반드시 제공되어야 의미가 생기는 의존성**(예: 화면 단위 NavController, 인증 토큰 제공자)은 기본값을 두지 않고 명시적으로 에러를 던지도록 정의해 두면, 누군가 Provider 설정을 빠뜨렸을 때 런타임이 즉시 알려 주어 사일런트한 버그가 생기지 않게 막을 수 있습니다.

</def>
</deflist>
