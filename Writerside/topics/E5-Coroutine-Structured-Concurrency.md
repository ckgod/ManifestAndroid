# E5) 코루틴과 구조적 동시성

## 코루틴 기초 다시 보기 {#C0}

코루틴(coroutine)은 **일시 중단(suspend)이 가능한 작업 단위**입니다. 스레드를 점유한 채 블로킹하지 않고, `suspend` 지점에서 자신의 실행을 멈췄다가 나중에 같은 지점부터 재개할 수 있습니다.

- **`suspend` 함수**: 호출 지점에서 코루틴을 일시 중단할 수 있는 함수입니다. 일반 함수에서는 호출할 수 없고, 코루틴 또는 다른 `suspend` 함수 안에서만 호출됩니다.
- **`launch`**: 결과값을 반환하지 않는 코루틴을 시작하는 빌더입니다. 반환 타입은 `Job`입니다.
- **`async`**: 결과값을 반환하는 코루틴을 시작하는 빌더입니다. 반환 타입은 `Deferred<T>`입니다.

이 토픽의 핵심은 이 코루틴들이 **어떻게 부모-자식 관계로 묶여 함께 살고 함께 죽는가**, 즉 **구조적 동시성**입니다.

## CoroutineScope와 Job {#C1}

### CoroutineScope란 {#scope-basics}

`CoroutineScope`는 **코루틴이 실행되는 범위이자 생명주기의 경계**입니다. 모든 코루틴 빌더(`launch`, `async`)는 `CoroutineScope`의 확장 함수이므로, 코루틴은 반드시 어떤 스코프 안에서만 시작할 수 있습니다.

스코프는 내부에 `CoroutineContext`를 가지며, 그 컨텍스트의 핵심 요소가 `Job`과 `CoroutineDispatcher`입니다.

```kotlin
// CoroutineScope는 CoroutineContext 하나를 감싼 인터페이스다
val scope = CoroutineScope(Job() + Dispatchers.Main)

scope.launch {
    // 이 코루틴은 scope의 Job을 부모로 가진다
}
```

### Job: 코루틴의 핸들이자 생명주기 {#job-handle}

`Job`은 **코루틴 하나의 생명주기를 제어하는 핸들**입니다. 코루틴을 취소(`cancel()`)하거나, 완료될 때까지 기다리거나(`join()`), 현재 상태(active/completing/cancelled/completed)를 조회할 수 있습니다.

`Job`은 다음과 같은 상태를 가집니다.

| 상태 | isActive | isCompleted | isCancelled |
|------|----------|-------------|-------------|
| New (지연 시작) | false | false | false |
| Active (실행 중) | true | false | false |
| Cancelling | false | false | true |
| Cancelled | false | true | true |
| Completed | false | true | false |

> `Completing`(본문은 끝났지만 자식 완료를 기다리는 중) 상태는 외부에서 관찰하면 `Active`와 구분되지 않습니다(`isActive=true`). 그래서 위 표에는 별도로 두지 않았습니다.

### Job 계층 구조 (부모-자식) {#job-hierarchy}

가장 중요한 메커니즘입니다. 어떤 코루틴 안에서 다시 코루틴을 시작하면, **새 코루틴의 Job은 자동으로 바깥 코루틴의 Job을 부모로 삼는 자식 Job**이 됩니다.

```kotlin
scope.launch {            // 부모 Job
    launch { /* 자식 A */ }
    launch { /* 자식 B */ }
}
```

이 계층은 다음 세 가지를 보장합니다.

1. **부모는 모든 자식이 끝날 때까지 완료되지 않는다.** 부모 코루틴 본문이 끝나도, 자식이 살아 있으면 부모 Job은 "Completing" 상태로 대기합니다.
2. **부모가 취소되면 모든 자식이 취소된다.** 취소는 계층을 따라 아래로 전파됩니다.
3. **자식의 처리되지 않은 예외는 부모로 전파되어 부모와 형제를 취소시킨다.** (단 `SupervisorJob`은 예외 — 뒤에서 다룹니다.)

이 세 가지 보장이 바로 **구조적 동시성**의 실체입니다.

## async/await와 병렬 분해 {#C2}

### async는 결과를 약속한다

`launch`가 "값이 없는 작업"을 던지는 빌더라면, `async`는 **나중에 결과값을 돌려줄 것을 약속(`Deferred`)하는 빌더**입니다. `Deferred<T>`는 결과를 담을 수 있는 `Job`이며, `await()`로 그 결과를 받습니다.

```kotlin
suspend fun loadUser(): User = coroutineScope {
    val deferred: Deferred<User> = async { api.fetchUser() }
    deferred.await()   // 결과가 준비될 때까지 일시 중단
}
```

### 병렬 분해(parallel decomposition)

병렬 분해란 **독립적인 여러 작업을 동시에 시작해 두고, 모든 결과를 모아 합치는** 패턴입니다. 서로 의존하지 않는 작업을 순차로 실행하면 시간이 합산되지만, `async`로 동시에 띄우면 가장 오래 걸리는 작업 시간만큼만 소요됩니다.

```kotlin
suspend fun loadDashboard(): Dashboard = coroutineScope {
    // 두 호출을 동시에 시작 — 여기서는 기다리지 않는다
    val user = async { api.fetchUser() }      // 200ms 걸린다고 가정
    val feed = async { api.fetchFeed() }      // 300ms 걸린다고 가정

    // await에서 비로소 결과를 모은다
    Dashboard(user.await(), feed.await())     // 총 ~300ms (500ms 아님)
}
```

### 순차 vs 병렬, 그리고 흔한 실수

`async` 직후 바로 `await()`를 붙이면 병렬성이 사라지고 순차 실행이 됩니다. 동시성을 얻으려면 **시작(`async`)과 대기(`await`)를 분리**해야 합니다.

```kotlin
// 잘못된 예 — 사실상 순차 (200ms + 300ms = 500ms)
val user = async { api.fetchUser() }.await()  // 여기서 끝까지 기다림
val feed = async { api.fetchFeed() }.await()
```

이런 단순 합산 작업이라면 `awaitAll`로 의도를 더 명확히 표현할 수 있습니다.

```kotlin
val results = listOf(
    async { api.fetchUser() },
    async { api.fetchFeed() }
).awaitAll()
```

### async의 예외는 await 시점에 던져진다

이 부분이 면접에서 자주 헷갈리는 지점입니다. `async`로 시작한 코루틴이 던진 예외는, **`await()`를 호출하는 순간 그 호출 지점으로 다시 던져집니다.** `await()`를 하지 않으면 호출자는 그 예외를 보지 못합니다.

다만 `await()` 여부와 무관하게, 자식의 실패는 **구조적 동시성 규칙에 따라 부모로도 전파되어** 스코프 전체를 취소시킵니다. (이 부모 전파를 막는 것이 `supervisorScope`입니다.) 즉 `async`의 예외에는 두 경로가 있습니다.

- `await()` 호출 지점으로 다시 던져지는 경로 (호출자가 직접 받음)
- 부모 Job으로 전파되어 스코프를 취소하는 경로 (구조적 동시성)

```kotlin
coroutineScope {
    val deferred = async { error("boom") }
    // await을 호출하든 안 하든, 이 예외는 부모(coroutineScope)로 전파되어
    // coroutineScope 전체가 취소되고 호출자에게 예외가 던져진다.
    deferred.await()
}
```

## 구조적 동시성(Structured Concurrency) {#C3}

### 정의

구조적 동시성이란 **모든 코루틴이 명확한 부모 스코프 안에서만 실행되며, 부모 스코프는 자신이 시작한 모든 자식 코루틴이 끝나기 전에는 완료되지 않는다**는 원칙입니다. 코루틴의 생명주기가 코드의 구조(스코프의 중괄호 범위)에 종속된다는 뜻입니다.

### 무엇을 보장하는가

구조적 동시성은 세 가지 문제를 구조적으로 해결합니다.

1. **누수 방지**: 스코프를 벗어난 채 백그라운드에 남는 코루틴이 생기지 않습니다. 스코프가 끝나려면 모든 자식이 끝나야 하기 때문입니다.
2. **취소 전파**: 스코프를 취소하면 그 안의 모든 코루틴이 한 번에 취소됩니다. 일일이 핸들을 추적할 필요가 없습니다.
3. **예외 전파**: 자식 하나가 실패하면 형제들을 취소하고 부모로 예외가 올라갑니다. 실패가 조용히 묻히지 않습니다.

### coroutineScope 빌더 {#coroutinescope-builder}

`coroutineScope { }`는 **새로운 자식 스코프를 만들어, 그 안의 모든 코루틴이 끝날 때까지 일시 중단되는** suspend 함수입니다. 위 `loadDashboard` 예시처럼 여러 `async`를 묶는 표준 도구입니다.

```kotlin
suspend fun doWork() {
    coroutineScope {              // 이 블록은 두 자식이 모두 끝나야 반환된다
        launch { taskA() }
        launch { taskB() }
    }
    // 여기 도달했다면 taskA, taskB는 모두 완료(또는 취소 처리)된 상태다
}
```

### 안드로이드에서의 구조적 동시성: viewModelScope

안드로이드의 `viewModelScope`, `lifecycleScope`는 구조적 동시성을 생명주기에 묶은 사례입니다. `viewModelScope`는 ViewModel이 `onCleared()`될 때 자신의 Job을 취소하므로, ViewModel이 사라지면 그 안에서 시작한 모든 코루틴이 자동으로 취소됩니다. 화면이 종료됐는데 네트워크 콜백이 죽은 ViewModel을 건드리는 누수를 구조적으로 막아 줍니다.

```kotlin
class MyViewModel : ViewModel() {
    fun load() {
        viewModelScope.launch {       // onCleared() 시 자동 취소
            val data = repository.fetch()
            _uiState.value = data
        }
    }
}
```

### 협력적 취소(cooperative cancellation)

구조적 동시성의 취소는 **강제 종료가 아니라 협력적**입니다. 취소는 코루틴의 `Job`에 "취소됨" 플래그를 세우고, 코루틴이 다음 **suspend 지점**에 도달할 때 `CancellationException`을 던지는 방식으로 동작합니다. 따라서 suspend 호출 없이 도는 무거운 연산은 취소 요청을 받아도 멈추지 않습니다.

```kotlin
launch {
    while (isActive) {       // 취소 상태를 직접 확인하거나
        doChunk()
        yield()              // suspend 지점을 제공해 취소가 작동하게 한다
    }
}
```

`CancellationException`은 정상적인 취소 신호이므로 삼키면 안 됩니다. `try/catch (e: Exception)`로 잡았다면 반드시 다시 던지거나, `CancellationException`만 별도로 통과시켜야 합니다.

## coroutineScope vs supervisorScope {#C4}

두 빌더의 차이는 단 하나, **자식 하나가 실패했을 때 형제와 부모로 실패를 전파하는가**입니다.

### coroutineScope: 실패가 전파된다 {#coroutinescope-fails}

`coroutineScope`가 만드는 스코프는 일반 `Job`을 씁니다. 자식 하나가 예외로 실패하면, **나머지 형제 자식이 모두 취소되고** 예외가 `coroutineScope` 밖으로 던져집니다. "전부 성공 아니면 전부 실패"가 필요한 작업에 적합합니다.

```kotlin
suspend fun loadAll() = coroutineScope {
    launch { taskA() }            // taskB가 실패하면 이 taskA도 취소된다
    launch { taskB() }            // 여기서 예외 → 형제 취소 + 스코프 전체 실패
}
```

### supervisorScope: 실패가 격리된다

`supervisorScope`는 내부적으로 `SupervisorJob`을 씁니다. **자식의 실패가 부모와 형제로 전파되지 않습니다.** 한 자식이 죽어도 다른 자식들은 계속 실행됩니다. 서로 독립적인 작업들을 동시에 돌리되 일부 실패를 허용하고 싶을 때 씁니다.

```kotlin
suspend fun loadIndependently() = supervisorScope {
    launch { loadAds() }          // 광고 로딩 실패해도
    launch { loadContent() }      // 본문 로딩은 계속된다
}
```

### 핵심 주의점: 예외 처리 책임도 달라진다

`supervisorScope`에서는 실패가 부모로 올라가지 않으므로, **각 자식이 자신의 예외를 스스로 처리해야** 합니다. 처리하지 않으면 부모로 전파되는 대신 그 자식 자신의 책임으로 남습니다. `supervisorScope`에 직속으로 `launch`된 자식은 루트 코루틴처럼 취급되어, 자신의 컨텍스트에 설치된 `CoroutineExceptionHandler`가 있으면 그쪽으로 가고 없으면 크래시로 이어집니다.

```kotlin
supervisorScope {
    launch {
        try {
            loadAds()
        } catch (e: Exception) {
            if (e is CancellationException) throw e   // 취소 신호는 통과
            log(e)                                    // 광고 실패는 여기서 흡수
        }
    }
    launch { loadContent() }
}
```

### 방향성에 대한 정확한 이해

`SupervisorJob`이 막는 것은 **자식 → 부모(위로)** 방향의 실패 전파입니다. **부모 → 자식(아래로)** 방향의 취소 전파는 그대로 동작합니다. 즉 `supervisorScope` 자체를 취소하면 그 안의 모든 자식은 여전히 함께 취소됩니다. 구조적 동시성의 "함께 죽는다" 보장은 supervisorScope에서도 유지되며, 단지 "한 자식의 실패가 형제를 죽이지 않는다"만 달라집니다.

| 구분 | coroutineScope | supervisorScope |
|------|----------------|------------------|
| 내부 Job | 일반 Job | SupervisorJob |
| 자식 실패 시 형제 | 함께 취소됨 | 영향 없음 (계속 실행) |
| 자식 실패 시 부모 | 부모로 전파 → 스코프 실패 | 부모로 전파 안 됨 |
| 부모 취소 시 자식 | 모두 취소 | 모두 취소 (동일) |
| 적합한 상황 | 전부 성공해야 하는 묶음 | 독립적 작업, 일부 실패 허용 |

## 요약 {#summary}

> **TL;DR** — 코루틴은 스코프와 Job 계층으로 묶여 생명주기를 공유합니다(구조적 동시성). 그 덕분에 코루틴 누수 방지·취소 전파·예외 전파가 구조적으로 보장됩니다. 병렬은 `async` 의 시작과 `await` 의 대기를 분리해야 얻어지고, 일부 실패를 허용하려면 `supervisorScope` 로 실패를 격리합니다.

1. **CoroutineScope와 Job**: 모든 코루틴은 스코프 안에서 시작되고, Job 계층(부모-자식)으로 묶여 생명주기를 공유한다.
2. **async/await와 병렬 분해**: 독립 작업을 `async`로 동시에 띄우고 `await`로 결과를 모은다. 시작과 대기를 분리해야 병렬이 된다.
3. **구조적 동시성**: 부모 스코프는 모든 자식이 끝나야 완료된다 — 누수 방지, 취소 전파, 예외 전파를 구조적으로 보장한다.
4. **coroutineScope vs supervisorScope**: 자식 실패의 위쪽(부모·형제) 전파 여부가 유일한 차이. supervisorScope는 실패를 격리하되 아래쪽 취소 전파는 유지한다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 구조적 동시성(structured concurrency)이 무엇이고, 어떤 문제를 해결해 주나요?">

구조적 동시성은 모든 코루틴이 명확한 부모 스코프 안에서만 실행되고, 부모 스코프는 자신이 시작한 모든 자식 코루틴이 끝나기 전에는 완료되지 않는다는 원칙입니다. 코루틴의 생명주기가 코드의 구조(스코프의 범위)에 종속된다는 뜻입니다.

이 원칙은 세 가지를 보장합니다. 첫째, 스코프를 벗어나 백그라운드에 남는 코루틴 누수를 막습니다. 둘째, 스코프를 취소하면 그 안의 모든 코루틴이 한 번에 취소되어 취소가 자동으로 전파됩니다. 셋째, 자식 하나가 실패하면 형제를 취소하고 부모로 예외가 올라가 실패가 조용히 묻히지 않습니다. 안드로이드의 `viewModelScope`가 대표적인 예로, ViewModel이 `onCleared()`되면 그 안의 모든 코루틴이 자동 취소됩니다.

</def>
<def title="Q) Job의 부모-자식 계층은 취소와 예외 전파에서 각각 어떻게 동작하나요?">

어떤 코루틴 안에서 다시 코루틴을 시작하면 새 Job은 바깥 Job을 부모로 삼는 자식이 됩니다. 이 계층에서 취소는 부모에서 자식으로 아래로 전파됩니다. 부모를 취소하면 모든 자식이 함께 취소되고, 부모는 자식들이 모두 끝나야 완료됩니다.

예외는 반대로 자식에서 부모로 위로 전파됩니다. 자식의 처리되지 않은 예외는 부모로 올라가 부모와 다른 형제 자식들을 취소시킵니다. 다만 부모가 `SupervisorJob`인 경우(`supervisorScope`)에는 이 위쪽 전파가 차단되어, 한 자식의 실패가 형제나 부모에게 영향을 주지 않습니다. 이때도 부모에서 자식으로의 취소 전파는 그대로 유지됩니다.

</def>
<def title="Q) async로 두 작업을 병렬 실행하려는데 시간이 단축되지 않습니다. 무엇이 문제일까요?">

`async` 직후에 바로 `await()`를 붙였을 가능성이 높습니다. `val a = async { ... }.await()`처럼 쓰면, 첫 작업이 끝날 때까지 기다린 뒤에야 다음 `async`가 시작되므로 사실상 순차 실행이 되어 시간이 합산됩니다.

병렬성을 얻으려면 시작과 대기를 분리해야 합니다. 먼저 `val a = async { ... }`, `val b = async { ... }`로 두 코루틴을 동시에 시작해 두고, 그 다음에 `a.await()`, `b.await()`로 결과를 모아야 합니다. 그러면 두 작업이 겹쳐 실행되어 더 오래 걸리는 작업 시간만큼만 소요됩니다. 단순 합산이라면 `listOf(a, b).awaitAll()`로 의도를 더 명확히 표현할 수 있습니다.

</def>
<def title="Q) coroutineScope와 supervisorScope의 차이는 무엇인가요? 언제 어떤 것을 쓰나요?">

차이는 자식 하나가 실패했을 때 그 실패를 형제와 부모로 위쪽으로 전파하는가입니다. `coroutineScope`는 일반 Job을 사용하므로, 자식 하나가 실패하면 나머지 형제가 모두 취소되고 예외가 스코프 밖으로 던져집니다. "전부 성공 아니면 전부 실패"가 필요한 묶음 작업에 적합합니다.

`supervisorScope`는 `SupervisorJob`을 사용해 자식의 실패가 부모와 형제로 전파되지 않습니다. 한 자식이 죽어도 다른 자식은 계속 실행되므로, 서로 독립적인 작업을 동시에 돌리되 일부 실패를 허용할 때 씁니다. 대신 실패가 위로 올라가지 않으므로 각 자식이 자신의 예외를 직접 처리해야 합니다. 한 가지 주의점은, supervisorScope가 막는 것은 위쪽(자식→부모) 전파뿐이고, 부모를 취소하면 자식들은 여전히 모두 함께 취소된다는 점입니다.

</def>
<def title="Q) 코루틴의 취소는 어떻게 동작하나요? CancellationException은 어떻게 다뤄야 하나요?">

코루틴 취소는 강제 종료가 아니라 협력적입니다. 취소는 코루틴의 Job에 취소 플래그를 세우고, 코루틴이 다음 suspend 지점에 도달할 때 `CancellationException`을 던지는 방식으로 동작합니다. 따라서 suspend 호출 없이 도는 무거운 연산은 취소 요청을 받아도 멈추지 않습니다. 이런 루프에서는 `isActive`를 직접 확인하거나 `yield()`, `ensureActive()` 같은 suspend 지점을 넣어 취소가 작동하게 해야 합니다.

`CancellationException`은 정상적인 취소 신호이므로 삼키면 안 됩니다. `try/catch (e: Exception)`로 광범위하게 잡는 코드에서는 `CancellationException`을 다시 던지도록 처리해야 합니다. 그렇지 않으면 부모가 보낸 취소가 무시되어 코루틴이 멈추지 않거나 구조적 동시성의 취소 보장이 깨집니다.

</def>
</deflist>
