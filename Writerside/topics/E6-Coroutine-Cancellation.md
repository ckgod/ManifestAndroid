# E6) 코루틴 취소와 예외 처리

## 취소는 어떻게 동작하는가 {#C0}

코루틴의 취소(cancellation)는 **강제 종료가 아니라 협력적(cooperative)**입니다. `Job`을 취소해도 실행 중인 코드가 그 자리에서 즉시 중단되는 것이 아니라, 코루틴이 다음 취소 확인 지점에 도달했을 때 비로소 멈춥니다.

메커니즘은 두 단계입니다.

1. `cancel()`을 호출하면 해당 `Job`의 상태가 `Cancelling`으로 바뀌고 내부 취소 플래그가 세워집니다(`isActive`가 `false`가 됩니다).
2. 코루틴이 **suspend 지점**에 도달하면, 그 지점에서 `CancellationException`이 던져지며 코루틴이 실제로 중단됩니다.

따라서 취소가 실제로 작동하려면 코루틴이 주기적으로 suspend 지점을 거쳐야 합니다. 이 토픽은 그 "협력"을 코드에서 어떻게 보장하는지, 그리고 취소 신호인 `CancellationException`을 예외 처리에서 어떻게 다뤄야 하는지를 다룹니다.

## 협력적 취소 (cooperative cancellation) {#C1}

### 왜 협력이 필요한가 {#why-cooperative}

JVM에는 스레드를 안전하게 강제 종료하는 방법이 없습니다(`Thread.stop()`은 모니터를 풀지 않고 죽여 상태를 깨뜨리므로 폐기됐습니다). 코루틴도 같은 이유로 강제 종료 대신 협력 방식을 택했습니다. 코드가 스스로 "지금 취소됐는가"를 확인하고 멈춰 줘야, 리소스 정리(`finally`)와 일관성을 보장할 수 있습니다.

문제는 **suspend 호출 없이 도는 CPU 연산은 취소를 확인할 틈이 없다**는 점입니다.

```kotlin
val job = launch(Dispatchers.Default) {
    var i = 0
    while (i < 1_000_000_000) {   // suspend 지점이 전혀 없는 순수 연산
        i++
    }
    // cancel()을 불러도 이 루프는 끝까지 돕니다
}
delay(100)
job.cancelAndJoin()  // 루프가 끝날 때까지 반환되지 않습니다
```

### 취소에 협력하는 세 가지 방법 {#cooperate-three-ways}

연산 루프가 취소에 반응하게 하려면, 취소를 확인하는 지점을 명시적으로 넣어야 합니다.

```kotlin
launch(Dispatchers.Default) {
    while (i < limit) {
        ensureActive()   // 취소됐으면 CancellationException을 던집니다
        compute(i)
        i++
    }
}
```

- **`isActive`**: 현재 코루틴이 활성인지 알려주는 `Boolean` 프로퍼티입니다. `while (isActive)`로 루프 조건에 직접 걸면, 취소 시 예외 없이 루프를 빠져나갑니다.
- **`ensureActive()`**: 취소됐으면 즉시 `CancellationException`을 던집니다. 취소를 "정상 종료"가 아니라 "예외로 중단"시키고 싶을 때 적합합니다.
- **`yield()`**: suspend 함수로, 취소를 확인하면서 동시에 다른 코루틴에 실행 기회를 양보합니다.

`kotlinx.coroutines`가 제공하는 모든 suspend 함수(`delay`, `withContext`, `await` 등)는 내부에서 이미 취소를 확인하므로, 그런 함수를 호출하는 코루틴은 별도 처리 없이 취소에 반응합니다. 협력 코드를 직접 넣어야 하는 경우는 **suspend 호출이 없는 긴 연산 루프**에 한정됩니다.

### 취소 후 정리: NonCancellable {#non-cancellable}

취소된 코루틴의 `finally` 블록 안에서 다시 suspend 함수를 호출하면, 이미 코루틴이 `Cancelling` 상태이므로 그 호출은 곧바로 `CancellationException`을 던지며 실패합니다. 취소 중에도 반드시 완료해야 하는 정리 작업(예: 자원 반납을 위한 마지막 네트워크 호출)은 `withContext(NonCancellable)`로 감쌉니다.

```kotlin
val job = launch {
    try {
        work()
    } finally {
        withContext(NonCancellable) {
            cleanupSuspend()   // 취소 상태에서도 끝까지 실행됩니다
        }
    }
}
```

## CancellationException {#C2}

### 취소의 신호이자 정상 흐름 {#cancellation-signal}

`CancellationException`은 코루틴 취소를 전달하는 **정상적인 제어 신호**입니다. 일반적인 실패 예외와 결정적으로 다른 점은, 코루틴 머신이 이 예외를 특별 취급한다는 것입니다.

- 코루틴이 `CancellationException`으로 끝나면 **실패(failure)가 아니라 정상 취소(cancelled)로 간주**됩니다.
- 그래서 이 예외는 **부모로 전파되어 부모·형제를 취소시키지 않습니다.** 자신이 받은 취소를 자기 자신이 처리하는 것이기 때문입니다.
- `CoroutineExceptionHandler`로도 가지 않습니다. 핸들러는 처리되지 않은 "진짜 예외"만 받습니다.

이 특수 취급 덕분에 한 코루틴의 취소가 다른 형제 코루틴을 잘못 죽이는 일이 없습니다. 일반 예외라면 자식의 실패가 부모로 올라가 형제를 취소시키지만, 취소는 그 코루틴 한 줄기에만 적용됩니다.

### 절대 삼키지 말 것 {#never-swallow}

`CancellationException`이 정상 신호라는 사실에는 중요한 책임이 따릅니다. **이 예외를 잡아서 삼키면 취소가 무력화됩니다.**

```kotlin
// 잘못된 코드 — 취소가 동작하지 않습니다
launch {
    try {
        repeat(1000) {
            delay(100)   // 취소 시 여기서 CancellationException 발생
        }
    } catch (e: Exception) {
        // CancellationException까지 여기서 흡수됩니다
        log("실패", e)   // 취소가 "처리됨"이 되어 코루틴이 계속 살아남습니다
    }
}
```

`catch (e: Exception)`은 `CancellationException`도 함께 잡습니다(상속 계층상 `CancellationException`은 `IllegalStateException` → ... → `Exception`의 하위입니다). 이를 삼키면 부모가 보낸 취소가 무시되어 코루틴이 멈추지 않고, 구조적 동시성의 취소 보장이 깨집니다.

올바른 처리는 **취소 예외만 다시 던지는 것**입니다.

```kotlin
launch {
    try {
        repeat(1000) { delay(100) }
    } catch (e: CancellationException) {
        throw e            // 취소 신호는 통과시킵니다
    } catch (e: Exception) {
        log("진짜 실패", e) // 그 외 예외만 처리합니다
    }
}
```

`catch (e: CancellationException) { throw e }`를 더 일반적인 `catch`보다 **위에** 두는 것이 핵심입니다. catch 절은 위에서부터 매칭되므로, 취소를 먼저 걸러내야 아래의 광범위한 catch가 취소를 삼키지 않습니다.

## runCatching 주의 {#C3}

### runCatching이 취소를 삼킨다 {#runcatching-swallows}

코틀린 표준 라이브러리의 `runCatching { }`은 블록에서 던져진 **모든 `Throwable`을 잡아 `Result.failure`로 감쌉니다.** 여기에는 `CancellationException`도 포함됩니다. 그래서 코루틴 안에서 `runCatching`을 그대로 쓰면, 위에서 본 "취소를 삼키는" 문제가 그대로 발생합니다.

```kotlin
// 위험 — runCatching이 CancellationException까지 Result로 가둡니다
viewModelScope.launch {
    val result = runCatching {
        repository.fetch()   // 취소 시 CancellationException 발생
    }
    // 코루틴이 취소됐는데도 여기로 흘러와 result.isFailure를 보고 동작합니다
    result.onFailure { showError() }
}
```

`runCatching`의 시그니처는 `inline fun <R> runCatching(block: () -> R): Result<R>`이며, 내부 구현이 `try { Result.success(block()) } catch (e: Throwable) { Result.failure(e) }`입니다. `Throwable`을 통째로 잡으므로 취소도 예외가 아니라 일반 실패로 둔갑합니다. 이것은 표준 라이브러리의 의도된 동작이지만, **코루틴 컨텍스트에서는 함정**입니다.

### 안전하게 쓰는 방법 {#runcatching-safe}

`runCatching`을 코루틴 안에서 쓰려면, 결과를 받은 직후 취소 예외를 다시 꺼내 던져야 합니다.

```kotlin
val result = runCatching { repository.fetch() }
    .onFailure { if (it is CancellationException) throw it }
```

반복적으로 필요하면 취소를 통과시키는 헬퍼를 두는 편이 안전합니다.

```kotlin
inline fun <R> runCatchingCoroutine(block: () -> R): Result<R> =
    try {
        Result.success(block())
    } catch (e: CancellationException) {
        throw e                       // 취소는 통과
    } catch (e: Throwable) {
        Result.failure(e)             // 그 외만 Result로 감쌈
    }
```

`coroutineContext.ensureActive()`를 `onFailure` 안에서 호출하는 방법도 있습니다. 이는 현재 컨텍스트가 취소됐는지 확인해 취소됐으면 `CancellationException`을 던지므로, 취소가 `runCatching`에 갇혔더라도 다시 표면화시킵니다. 핵심 원칙은 동일합니다. **`Throwable`이나 `Exception`을 광범위하게 잡는 모든 코드는 코루틴 안에서 취소를 별도로 통과시켜야 합니다.**

## SupervisorJob {#C4}

### 일반 Job과의 차이 {#job-vs-supervisor}

`SupervisorJob`은 **자식의 실패를 부모와 형제로 전파하지 않는 Job**입니다. 일반 `Job`은 자식 하나가 (취소가 아닌) 예외로 실패하면 그 예외를 부모로 올려 부모와 모든 형제를 취소시킵니다. `SupervisorJob`은 이 **위쪽(자식 → 부모) 실패 전파만 차단**합니다.

방향을 정확히 구분하는 것이 중요합니다.

- **자식 → 부모(위) 실패 전파**: `SupervisorJob`이 차단합니다. 한 자식이 죽어도 형제와 부모는 멀쩡합니다.
- **부모 → 자식(아래) 취소 전파**: 그대로 동작합니다. `SupervisorJob`을 취소하면 모든 자식이 함께 취소됩니다.

즉 구조적 동시성의 "부모가 죽으면 자식도 함께 죽는다"는 보장은 유지되고, 단지 "한 자식의 실패가 형제를 죽이지 않는다"만 추가됩니다.

### supervisorScope와 예외 처리 책임 {#supervisor-scope}

가장 흔한 사용 형태는 `supervisorScope { }` 빌더입니다. 내부적으로 `SupervisorJob`을 쓰는 자식 스코프를 만들어, 서로 독립적인 작업을 동시에 돌리되 일부 실패를 허용합니다.

```kotlin
suspend fun loadScreen() = supervisorScope {
    launch { loadAds() }       // 광고 로딩이 실패해도
    launch { loadContent() }   // 본문 로딩은 계속됩니다
}
```

실패가 위로 올라가지 않으므로, **각 자식이 자신의 예외를 스스로 처리해야** 합니다. 처리하지 않으면 그 예외는 부모로 전파되는 대신 자식 자신의 책임으로 남습니다. `supervisorScope`에 직속으로 `launch`된 자식은 루트 코루틴처럼 취급되어, 컨텍스트에 `CoroutineExceptionHandler`가 설치돼 있으면 그쪽으로 가고 없으면 처리되지 않은 예외가 됩니다.

```kotlin
supervisorScope {
    launch {
        try {
            loadAds()
        } catch (e: CancellationException) {
            throw e          // 취소 신호는 통과
        } catch (e: Exception) {
            log(e)           // 광고 실패는 여기서 흡수
        }
    }
    launch { loadContent() }
}
```

### SupervisorJob을 직접 쓸 때의 함정 {#supervisor-pitfall}

`SupervisorJob`을 스코프 생성자에 직접 넣어 쓸 수도 있는데, 이때 주의할 점이 있습니다. **감독(supervision) 효과는 그 `SupervisorJob`을 직접 부모로 가진 자식에게만 적용됩니다.**

```kotlin
val scope = CoroutineScope(SupervisorJob())

// 직속 자식 — 실패가 격리됩니다
scope.launch { mayFail() }    // 이게 죽어도 아래 launch에는 영향이 없습니다
scope.launch { keepRunning() }

// 그러나 한 단계 안으로 들어가면 일반 Job 규칙입니다
scope.launch {
    launch { childA() }       // 여기 두 자식은 일반 Job 관계이므로
    launch { childB() }       // childA가 실패하면 childB도 취소됩니다
}
```

바깥 `scope.launch { }`가 만드는 코루틴의 `Job`은 일반 `Job`이지 `SupervisorJob`이 아닙니다. 따라서 그 안에서 다시 시작한 손자 코루틴들 사이에서는 보통의 "형제 동반 취소"가 그대로 적용됩니다. 안드로이드의 `viewModelScope`도 내부적으로 `SupervisorJob`을 사용하므로, ViewModel에서 직접 띄운 코루틴들은 서로 독립적이지만 그 안에서 묶은 자식들은 일반 규칙을 따릅니다.

## 요약 {#summary}

> **TL;DR** — 코루틴 취소는 강제 종료가 아니라 협력적이어서, 코루틴이 suspend 지점이나 `isActive`/`ensureActive()`로 취소를 확인할 때 비로소 멈춥니다. 취소 신호인 `CancellationException`은 정상 흐름이라 부모로 전파되지 않으며, 절대 삼키면 안 됩니다 — `catch (e: Exception)`이나 `runCatching`은 이 신호까지 잡아 취소를 무력화하므로 취소만 별도로 다시 던져야 합니다. `SupervisorJob`은 자식 → 부모 위쪽 실패 전파만 차단하고, 부모 → 자식 아래쪽 취소 전파는 그대로 유지합니다.

1. **협력적 취소**: 취소는 플래그만 세우고, 코루틴이 suspend 지점에 도달해야 실제로 멈춘다. suspend 없는 연산 루프는 `isActive`/`ensureActive()`/`yield()`로 직접 협력해야 한다.
2. **CancellationException**: 취소를 전달하는 정상 신호로, 부모로 전파되지 않고 핸들러로도 가지 않는다. 삼키면 취소가 무력화되므로 광범위한 catch에서는 반드시 다시 던진다.
3. **runCatching 주의**: `runCatching`은 `Throwable`을 통째로 잡아 `CancellationException`까지 `Result`에 가둔다. 코루틴 안에서는 취소만 다시 던지는 헬퍼나 `ensureActive()`로 표면화해야 한다.
4. **SupervisorJob**: 자식 → 부모(위) 실패 전파만 차단하고, 부모 → 자식(아래) 취소 전파는 유지한다. 감독 효과는 직속 자식에게만 적용된다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 코루틴 취소가 협력적이라는 말은 무슨 뜻인가요? cancel()을 불러도 멈추지 않는 코드는 어떤 경우인가요?">

협력적 취소란 `cancel()`이 코드를 즉시 강제 종료하는 것이 아니라, 코루틴의 `Job`에 취소 플래그(`isActive`가 `false`로)만 세우고, 코루틴이 다음 suspend 지점에 도달할 때 그곳에서 `CancellationException`을 던져 멈추는 방식을 말합니다. JVM에 스레드를 안전하게 강제 종료하는 수단이 없기 때문에, 리소스 정리와 일관성을 보장하려면 코드가 스스로 취소를 확인하고 멈춰 줘야 합니다.

멈추지 않는 대표적인 경우는 suspend 호출이 전혀 없는 순수 CPU 연산 루프입니다. `while (i < limit) { compute(i); i++ }`처럼 도는 코드는 취소를 확인할 틈이 없어 끝까지 실행됩니다. 이런 루프는 `while (isActive)`로 조건을 걸거나, 루프 안에서 `ensureActive()` 또는 `yield()`를 호출해 취소 확인 지점을 명시적으로 넣어야 합니다.

</def>
<def title="Q) CancellationException은 다른 예외와 무엇이 다른가요? 왜 삼키면 안 되나요?">

`CancellationException`은 실패를 알리는 일반 예외가 아니라 취소를 전달하는 정상적인 제어 신호입니다. 코루틴 머신이 이 예외를 특별 취급하여, 이 예외로 끝난 코루틴은 실패가 아니라 정상 취소로 간주됩니다. 그래서 부모로 전파되어 부모나 형제를 취소시키지 않고, `CoroutineExceptionHandler`로도 가지 않습니다.

삼키면 안 되는 이유는, 이 예외가 부모가 보낸 취소 요청 그 자체이기 때문입니다. `catch (e: Exception)`처럼 광범위하게 잡아 흡수하면, 취소가 "처리됨"으로 끝나 코루틴이 멈추지 않고 계속 살아남습니다. 결과적으로 구조적 동시성의 취소 보장이 깨집니다. 올바른 처리는 취소 예외를 먼저 걸러 다시 던지는 것입니다. `catch (e: CancellationException) { throw e }`를 더 일반적인 catch보다 위에 두어야 합니다.

</def>
<def title="Q) 코루틴 안에서 runCatching을 쓸 때 어떤 문제가 생기나요?">

`runCatching`은 블록에서 던져진 모든 `Throwable`을 잡아 `Result.failure`로 감쌉니다. 구현이 `catch (e: Throwable)`이기 때문에 `CancellationException`까지 잡아 `Result`에 가둡니다. 그래서 코루틴이 취소되어 `CancellationException`이 발생해도, `runCatching`이 그것을 일반 실패처럼 `Result.failure`로 만들어 버립니다. 코드는 취소된 줄 모르고 `result.isFailure`를 보고 에러 UI를 띄우는 등 잘못된 동작을 합니다. 즉 취소가 무력화됩니다.

해결책은 결과를 받은 직후 취소 예외를 다시 표면화하는 것입니다. `.onFailure { if (it is CancellationException) throw it }`를 붙이거나, `onFailure` 안에서 `coroutineContext.ensureActive()`를 호출합니다. 반복된다면 `catch (e: CancellationException) { throw e }`를 먼저 두고 그 외 `Throwable`만 `Result`로 감싸는 헬퍼를 만들어 쓰는 편이 안전합니다.

</def>
<def title="Q) SupervisorJob은 무엇을 막고 무엇을 막지 않나요?">

`SupervisorJob`은 자식의 실패가 위로(자식 → 부모) 전파되는 것만 차단합니다. 일반 `Job`은 자식 하나가 예외로 실패하면 부모로 올려 부모와 모든 형제를 취소시키지만, `SupervisorJob`에서는 한 자식이 죽어도 형제와 부모가 멀쩡합니다.

반면 부모에서 자식으로(부모 → 자식) 내려가는 취소 전파는 그대로 동작합니다. `SupervisorJob`을 취소하면 그 자식들은 모두 함께 취소됩니다. 즉 구조적 동시성의 "부모가 죽으면 자식도 함께 죽는다"는 보장은 유지되고, "한 자식의 실패가 형제를 죽이지 않는다"만 추가됩니다. 또한 실패가 위로 올라가지 않으므로 각 자식이 자신의 예외를 직접 처리해야 합니다.

</def>
<def title="Q) SupervisorJob을 스코프에 직접 넣었는데, 안쪽 자식들이 여전히 함께 취소됩니다. 왜 그런가요?">

감독 효과는 그 `SupervisorJob`을 직접 부모로 가진 직속 자식에게만 적용되기 때문입니다. `CoroutineScope(SupervisorJob())`에서 `scope.launch { }`로 띄운 코루틴들끼리는 서로 격리됩니다. 그러나 그중 한 `launch` 블록 안에서 다시 `launch`로 손자 코루틴을 여러 개 시작하면, 그 손자들의 부모는 바깥 `launch`가 만든 일반 `Job`이지 `SupervisorJob`이 아닙니다.

따라서 손자들 사이에서는 일반 `Job`의 규칙, 즉 한 형제가 실패하면 다른 형제도 취소되는 동작이 그대로 적용됩니다. 안쪽까지 실패를 격리하려면 그 안에서 다시 `supervisorScope { }`를 쓰거나, 각 손자를 `SupervisorJob` 컨텍스트로 시작해야 합니다.

</def>
</deflist>
