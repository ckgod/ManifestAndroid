# Q16) rememberUpdatedState

## rememberUpdatedState의 목적은 무엇이며 어떻게 동작하나요? {#what-is-remember-updated-state}

[`rememberUpdatedState`](https://developer.android.com/develop/ui/compose/side-effects#rememberupdatedstate)는 Composition 컨텍스트에서 상태 업데이트를 안전하게 처리하기 위한 유틸리티 함수입니다. 람다나 콜백이 이전 리컴포지션에서 생성된 경우에도 항상 최신 상태 값이 사용되도록 보장합니다. 이를 통해 오래된 상태 참조로 인한 버그를 예방할 수 있습니다.

### 발생하는 문제와 해결책 {#problem-and-solution}

Composable에서 콜백이나 람다를 생성하면, 해당 함수가 이미 Compose된 이후에는 내부에서 참조하는 상태 값이 자동으로 갱신되지 않을 수 있습니다. `rememberUpdatedState`는 상태의 최신 값을 항상 유지하는 메커니즘을 제공하여 이 문제를 해결합니다.

함수 시그니처는 다음과 같습니다.

```kotlin
@Composable
fun <T> rememberUpdatedState(newValue: T): State<T>
```
{title="rememberUpdatedState.kt"}

### 사용 예시 {#usage-example}

`rememberUpdatedState`는 다음 상황에서 특히 유용합니다.

1. **장시간 실행되는 이펙트에 콜백을 전달할 때**: 이전 Composition에서 생성된 람다나 콜백이 최신 상태를 사용해야 하는 경우입니다.
2. **애니메이션 또는 사이드 이펙트 API와 함께 사용할 때**: `LaunchedEffect`, `DisposableEffect` 등 리컴포지션 이후에도 지속되는 API와 함께 사용합니다.

```kotlin
@Composable
fun TimerWithCallback(
    onTimeout: () -> Unit,
    timeoutMillis: Long = 5000L
) {
    val currentOnTimeout by rememberUpdatedState(onTimeout)

    // TimerWithCallback의 생명주기에 맞는 이펙트를 생성합니다.
    // 리컴포지션이 발생해도 delay가 다시 시작되지 않습니다.
    LaunchedEffect(true) {
        delay(timeoutMillis)
        currentOnTimeout() // 항상 최신 콜백이 호출됩니다
    }

    Text(text = "Timer running for $timeoutMillis milliseconds")
}
```
{title="RememberUpdatedStateExample.kt"}

### 오래된 콜백 문제가 발생하는 과정 {#stale-callback-problem}

이 문제를 이해하려면 Compose의 리컴포지션과 `LaunchedEffect`의 동작 방식을 함께 살펴봐야 합니다.

상위 Composable의 상태가 변하여 리컴포지션이 발생하면, Compose는 `TimerWithCallback`을 다시 호출하면서 최신 상태를 반영한 새로운 `onTimeout` 람다 인스턴스를 전달합니다. 함수 시그니처가 `() -> Unit`으로 동일해 보이더라도, 내부에서 참조하는 데이터가 달라졌다면 실질적으로 다른 함수 객체입니다.

그런데 `LaunchedEffect(true)` 또는 `LaunchedEffect(Unit)`은 키 값이 변하지 않으므로 최초 Composition 시 단 한 번만 실행되며, 이후 리컴포지션에서는 재시작되지 않습니다. 바로 이 특성 때문에 다음과 같은 문제가 발생합니다.

1. **최초 실행과 캡처**: 최초 Composition 시 `LaunchedEffect`가 실행됩니다. 코루틴 블록은 초기 `onTimeout`을 캡처한 채로 `delay(5000L)` 대기에 들어갑니다.
2. **리컴포지션 발생**: 5초가 지나기 전에 상위 상태가 변하여 새로운 `onTimeout` 함수가 하위 Composable로 전달됩니다.
3. **재시작 생략**: `LaunchedEffect`의 키가 `true`이므로 진행 중인 `delay`는 취소되거나 재시작되지 않고 계속 실행됩니다.
4. **오래된 콜백 실행**: 5초가 지나 콜백을 실행할 때, `LaunchedEffect`는 최신 `onTimeout`이 아닌 최초에 캡처해 두었던 낡은 콜백을 실행합니다. 결과적으로 과거 데이터를 기반으로 한 잘못된 로직이 처리됩니다.

`rememberUpdatedState`를 사용하면, `LaunchedEffect`가 참조하는 `currentOnTimeout`이 리컴포지션마다 자동으로 갱신되므로 이 문제를 깔끔하게 해결할 수 있습니다.

### 주요 장점 {#key-benefits}

- **오래된 상태 방지**: 장시간 실행되는 이펙트에서 상태 참조가 만료되어 발생하는 버그를 예방합니다.
- **안전한 Composition 처리**: `LaunchedEffect`, `DisposableEffect` 등 Composition 인식 API와 자연스럽게 연동됩니다.
- **간단한 통합**: 최소한의 코드 변경으로 상태가 항상 최신 값을 반영하도록 보장합니다.

### 요약 {#summary}

<tldr>
`rememberUpdatedState`는 콜백이나 장시간 실행되는 이펙트에서 상태 업데이트를 관리하는 사이드 이펙트 핸들러 API입니다. 가장 최근의 상태 값이 항상 사용되도록 보장하여 오래된 데이터로 인한 잠재적 문제를 방지합니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) LaunchedEffect를 사용하여 지연 동작을 트리거하는 Composable에서, 지연 후 항상 최신 람다가 호출되도록 하려면 어떻게 해야 하나요?">

`rememberUpdatedState`를 사용하여 람다를 래핑하면 됩니다. `LaunchedEffect`의 키를 `true`나 `Unit`으로 고정하면 리컴포지션 시 이펙트가 재시작되지 않지만, `rememberUpdatedState`로 캡처한 콜백은 항상 최신 값을 참조합니다.

```kotlin
@Composable
fun DelayedAction(onAction: () -> Unit) {
    val currentOnAction by rememberUpdatedState(onAction)

    LaunchedEffect(Unit) {
        delay(3000L)
        currentOnAction() // 리컴포지션이 발생해도 최신 onAction이 호출됩니다
    }
}
```
{title="DelayedAction.kt"}

`LaunchedEffect(onAction)` 처럼 람다 자체를 키로 사용하면 람다가 바뀔 때마다 이펙트가 재시작되어 의도하지 않은 동작이 발생할 수 있습니다. `rememberUpdatedState`를 사용하면 이펙트는 한 번만 시작되면서 최신 콜백을 안전하게 참조할 수 있습니다.

</def>
</deflist>
