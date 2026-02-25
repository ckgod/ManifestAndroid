# Details: produceState 내부 구현

## produceState는 내부적으로 어떻게 구현되어 있나요? {#produce-state-internals}

`produceState`의 내부 구현을 살펴보면 흥미로운 사실을 발견할 수 있습니다. 외부에서 보기에는 독립적인 API처럼 보이지만, 실제로는 이미 친숙한 두 가지 Compose 메커니즘을 조합하여 구현되어 있습니다.

### 내부 구현 코드 {#internal-implementation}

```kotlin
@Composable
fun <T> produceState(
    initialValue: T,
    key1: Any?,
    producer: suspend ProduceStateScope<T>.() -> Unit
): State<T> {
    val result = remember { mutableStateOf(initialValue) }
    LaunchedEffect(key1) {
        ProduceStateScopeImpl(result, coroutineContext).producer()
    }
    return result
}

private class ProduceStateScopeImpl<T>(
    state: MutableState<T>,
    override val coroutineContext: CoroutineContext
) : ProduceStateScope<T>, MutableState<T> by state {

    override suspend fun awaitDispose(onDispose: () -> Unit): Nothing {
        try {
            suspendCancellableCoroutine<Nothing> { }
        } finally {
            onDispose()
        }
    }
}
```
{title="produceState.kt"}

### 동작 원리 분석 {#how-it-works-internally}

`produceState`의 구현은 두 가지 핵심 요소로 구성됩니다.

**1. `remember { mutableStateOf(initialValue) }`**

`remember`와 `mutableStateOf`를 사용하여 Composition에 연결된 상태 객체를 생성합니다. 이 상태 객체가 프로듀서 코루틴이 값을 업데이트할 때 Composable의 리컴포지션을 트리거합니다.

**2. `LaunchedEffect(key1)`**

`LaunchedEffect`를 사용하여 프로듀서 코루틴을 안전하게 실행합니다. 이를 통해 `produceState`는 다음과 같은 특성을 자동으로 갖게 됩니다.

- **자동 취소**: Composable이 Composition을 떠나면 `LaunchedEffect`가 코루틴을 자동으로 취소합니다.
- **키 기반 재시작**: `key1` 값이 변경되면 기존 코루틴이 취소되고 새 코루틴이 시작됩니다.

### ProduceStateScopeImpl과 awaitDispose {#produce-state-scope-impl}

`ProduceStateScopeImpl`은 `ProduceStateScope<T>`를 구현하는 내부 클래스입니다. `MutableState<T> by state`를 통해 델리게이션 패턴으로 상태 업데이트 기능을 위임받으므로, 프로듀서 람다 안에서 `value = ...` 형태로 직접 상태를 업데이트할 수 있습니다.

`awaitDispose`는 코루틴을 영구적으로 일시 정지시키는 특별한 함수입니다. `suspendCancellableCoroutine`으로 코루틴을 대기 상태에 두고, 코루틴이 취소될 때 `finally` 블록에서 `onDispose` 콜백을 실행합니다. 이를 통해 리소스 정리 로직을 안전하게 처리할 수 있습니다.

```kotlin
// awaitDispose 사용 예시
@Composable
fun LocationTracker(): State<Location?> {
    return produceState<Location?>(initialValue = null) {
        val locationClient = LocationClient()
        locationClient.startTracking { location ->
            value = location
        }
        // Composable이 사라질 때까지 대기하다가, 취소 시 정리 작업 수행
        awaitDispose {
            locationClient.stopTracking()
        }
    }
}
```
{title="AwaitDisposeExample.kt"}

### 요약 {#summary}

<tldr>
`produceState`는 내부적으로 `remember + mutableStateOf`로 상태를 생성하고, `LaunchedEffect`로 프로듀서 코루틴을 실행하는 조합으로 구현됩니다. 복잡해 보이는 API지만 기존 Compose 메커니즘을 재활용한 단순하고 효율적인 구현이며, `awaitDispose`를 통해 리소스 정리까지 선언적으로 처리할 수 있습니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) produceState를 직접 구현한다면 어떻게 작성할 수 있나요?">

내부 구현을 이해하면 동일한 동작을 직접 작성할 수 있습니다.

```kotlin
@Composable
fun <T> myProduceState(
    initialValue: T,
    key: Any?,
    producer: suspend () -> T
): State<T> {
    val state = remember { mutableStateOf(initialValue) }
    LaunchedEffect(key) {
        state.value = producer()
    }
    return state
}
```
{title="MyProduceState.kt"}

이는 공식 구현의 간소화 버전으로, 핵심 동작(상태 생성 + LaunchedEffect로 코루틴 실행)은 동일합니다. 공식 구현은 여기에 `ProduceStateScopeImpl`을 통한 `awaitDispose` 지원과 `vararg keys` 처리가 추가되어 있습니다.

</def>
</deflist>
