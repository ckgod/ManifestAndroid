# Q74) 복원력 설계

## 복원력이란 무엇인가 {#what-is-resilience}

복원력(resilience)이란 **시스템의 일부 구성 요소가 실패하거나 느려져도, 앱이 전체로서 동작 가능한 상태를 유지하는 능력**입니다. 안드로이드 앱은 신뢰할 수 없는 환경 위에서 동작합니다. 네트워크는 끊기고, 서버는 5xx를 반환하고, 응답은 수 초씩 지연되며, 사용자는 지하철·엘리베이터에서 연결이 사라진 채로 앱을 켭니다.

복원력 설계의 전제는 명확합니다. **실패는 예외 상황이 아니라 정상적으로 발생하는 사건**입니다. 따라서 "실패하지 않게 만드는 것"이 목표가 아니라, **실패가 발생했을 때 그 영향을 국소화하고 사용자에게 의미 있는 결과를 주는 것**이 목표입니다.

이 토픽은 그 목표를 이루는 세 가지 축을 다룹니다.

1. **부분 실패 허용**: 한 부분의 실패가 화면 전체를 무너뜨리지 않게 합니다.
2. **폴백·재시도**: 실패한 작업을 자동으로 다시 시도하거나, 대체 결과로 메웁니다.
3. **offline 우선**: 네트워크를 선택적 요소로 두고, 로컬 데이터를 단일 진실 공급원으로 삼습니다.

## 부분 실패 허용 {#partial-failure-tolerance}

### 부분 실패란 {#what-is-partial-failure}

부분 실패(partial failure)란 **여러 독립적인 작업 중 일부만 실패한 상태**입니다. 대시보드 화면이 사용자 정보, 피드, 광고 배너 세 가지를 각각 다른 API에서 가져온다고 할 때, 광고 API만 죽는 상황이 전형적인 부분 실패입니다.

복원력 없는 설계에서는 이 부분 실패가 **전체 실패로 번집니다.** 세 호출을 하나의 묶음으로 처리하면, 광고 하나가 실패했을 뿐인데 화면 전체가 에러 화면으로 바뀝니다. 부분 실패 허용은 이 전파를 끊어, **성공한 부분은 보여 주고 실패한 부분만 격리**하는 설계입니다.

### 실패를 격리하는 코루틴 구조 {#isolating-with-supervisor}

코루틴에서 핵심 도구는 `supervisorScope`입니다. 일반 `coroutineScope`는 자식 하나가 실패하면 형제 자식을 모두 취소하고 예외를 위로 던집니다. `supervisorScope`는 자식의 실패가 부모·형제로 전파되지 않으므로, 한 작업이 죽어도 나머지는 계속 진행됩니다.

```kotlin
suspend fun loadDashboard(): DashboardState = supervisorScope {
    // 세 작업을 독립적으로 시작 — 하나가 죽어도 나머지는 산다
    val user = async { runCatching { api.fetchUser() } }
    val feed = async { runCatching { api.fetchFeed() } }
    val ads  = async { runCatching { api.fetchAds() } }

    DashboardState(
        user = user.await().getOrNull(),   // 실패 시 null
        feed = feed.await().getOrDefault(emptyList()),
        ads  = ads.await().getOrNull(),    // 광고 실패는 화면에 영향 없음
    )
}
```

여기서 두 가지가 결합돼 있습니다.

- **`supervisorScope`**: 한 자식의 실패가 다른 자식을 취소하지 않게 합니다(아래로의 취소 전파는 유지되지만, 위로의 실패 전파는 차단됩니다).
- **`runCatching`**: 각 자식 안에서 예외를 `Result`로 포착해, await 지점에서 예외가 다시 던져지지 않고 값으로 다뤄지게 합니다.

`supervisorScope`만 쓰고 자식 안에서 예외를 포착하지 않으면, 그 자식은 루트 코루틴처럼 취급돼 `CoroutineExceptionHandler`로 가거나 크래시로 이어집니다. 따라서 **부분 실패를 화면 상태로 바꾸려면 자식 내부에서 예외를 잡아 값으로 변환**해야 합니다.

### CancellationException은 예외 처리에서 제외한다 {#exclude-cancellation}

`runCatching`이나 `try/catch (e: Exception)`는 `CancellationException`까지 삼킵니다. `CancellationException`은 정상적인 취소 신호이므로 흡수하면 안 됩니다. 직접 `try/catch`를 쓸 때는 취소를 다시 던져야 합니다.

```kotlin
try {
    api.fetchUser()
} catch (e: CancellationException) {
    throw e                  // 취소 신호는 통과시킨다
} catch (e: Exception) {
    null                     // 그 외 실패만 흡수
}
```

### UI 상태로 부분 실패를 표현한다 {#partial-state-modeling}

부분 실패를 제대로 다루려면 UI 상태 모델 자체가 **섹션별 성공/실패를 표현**할 수 있어야 합니다. 화면 전체를 하나의 `Loading/Success/Error`로만 모델링하면 부분 실패를 담을 자리가 없습니다.

```kotlin
data class DashboardState(
    val user: User?,                 // null이면 사용자 영역만 에러 표시
    val feed: List<Post>,            // 비었으면 빈 피드 표시
    val ads: Ad?,                    // null이면 광고 영역만 숨김
)
```

이렇게 두면 사용자 정보가 실패해도 피드는 정상적으로 보여 줄 수 있고, 실패한 영역만 재시도 버튼이나 자리 표시자로 처리할 수 있습니다.

## 폴백과 재시도 {#fallback-and-retry}

### 재시도: 일시적 실패를 자동으로 만회한다 {#retry-transient}

재시도(retry)는 **일시적(transient) 실패를 자동으로 다시 시도해 복구**하는 전략입니다. 네트워크 순간 끊김, 일시적 5xx, 타임아웃처럼 다시 시도하면 성공할 가능성이 있는 실패에 적합합니다.

재시도에는 두 가지 원칙이 있습니다.

1. **재시도 가능한 실패만 재시도한다.** HTTP 4xx(400, 401, 404 등)는 요청 자체가 잘못된 것이므로 재시도해도 같은 결과입니다. 재시도는 5xx, 타임아웃, 연결 실패 같은 일시적 오류에만 적용합니다.
2. **지수 백오프(exponential backoff)를 쓴다.** 실패 직후 즉시·동일 간격으로 반복하면 이미 부하를 받은 서버를 더 압박합니다. 재시도 간격을 점점 늘려(예: 1초 → 2초 → 4초) 서버에 회복할 여유를 줍니다. 여기에 약간의 무작위 지연(jitter)을 더하면, 동시에 실패한 다수 클라이언트가 같은 시점에 몰려 재시도하는 현상을 분산할 수 있습니다.

```kotlin
suspend fun <T> retryWithBackoff(
    maxAttempts: Int = 3,
    initialDelayMs: Long = 1_000,
    factor: Double = 2.0,
    block: suspend () -> T,
): T {
    var delayMs = initialDelayMs
    repeat(maxAttempts - 1) {
        try {
            return block()
        } catch (e: CancellationException) {
            throw e                              // 취소는 재시도하지 않는다
        } catch (e: IOException) {               // 일시적 실패만 재시도
            delay(delayMs + Random.nextLong(0, 250))   // 백오프 + jitter
            delayMs = (delayMs * factor).toLong()
        }
    }
    return block()                               // 마지막 시도는 예외를 그대로 던진다
}
```

`delay`는 suspend 함수이므로 스레드를 블로킹하지 않고, 코루틴이 취소되면 즉시 `CancellationException`으로 빠져나옵니다. Flow를 쓴다면 표준 연산자 `retry(retries) { cause -> ... }` 또는 `retryWhen`으로 같은 정책을 선언적으로 표현할 수 있습니다.

```kotlin
flow { emit(api.fetchUser()) }
    .retry(retries = 2) { cause -> cause is IOException }   // 조건부 재시도
```

### 폴백: 실패해도 의미 있는 대체값을 준다 {#fallback-value}

폴백(fallback)은 **주된 작업이 실패했을 때 대체 결과로 메우는** 전략입니다. 재시도가 "같은 일을 다시"라면, 폴백은 "다른 결과로 대신"입니다. 대표적인 폴백 원천은 다음과 같습니다.

- **캐시된 마지막 성공값**: 네트워크가 실패하면 직전에 받아 둔 로컬 데이터를 보여 줍니다.
- **기본값/빈 값**: 광고 로딩 실패 시 빈 배너, 추천 목록 실패 시 빈 리스트.
- **대체 경로**: 1차 엔드포인트 실패 시 2차 엔드포인트 또는 저해상도 리소스.

```kotlin
suspend fun getUser(): User =
    runCatching { api.fetchUser() }          // 1차: 네트워크
        .recoverCatching { localDao.lastUser() }   // 2차: 로컬 캐시
        .getOrDefault(User.GUEST)            // 3차: 게스트 기본값
```

폴백 설계에서 중요한 점은 **폴백이 발생했다는 사실을 사용자에게 알릴지 결정**하는 것입니다. 캐시된 오래된 데이터를 보여 준다면 "오프라인 데이터입니다" 같은 표시를 함께 두는 편이 정확합니다. 폴백을 조용히 적용하면 사용자가 최신 데이터로 오해할 수 있습니다.

### 재시도와 폴백의 결합, 그리고 멱등성 {#combine-and-idempotency}

실무에서는 둘을 단계로 결합합니다. **먼저 재시도로 일시적 실패를 만회하고, 그래도 실패하면 폴백으로 메우는** 순서입니다.

```kotlin
suspend fun loadUser(): User =
    runCatching { retryWithBackoff { api.fetchUser() } }   // 재시도 후
        .recoverCatching { localDao.lastUser() }           // 실패하면 폴백
        .getOrDefault(User.GUEST)
```

단, 재시도에는 전제가 있습니다. **재시도하는 작업은 멱등(idempotent)해야 합니다.** GET 조회는 여러 번 실행해도 안전하지만, "결제 실행"이나 "주문 생성" 같은 쓰기 작업은 재시도가 중복 실행을 일으킬 수 있습니다. 이런 작업은 서버가 멱등성 키(idempotency key)를 받아 중복을 무시하도록 설계돼 있어야만 안전하게 재시도할 수 있습니다.

## offline 우선 설계 {#offline-first}

### offline 우선이란 {#what-is-offline-first}

offline 우선(offline-first)이란 **로컬 저장소를 단일 진실 공급원(single source of truth)으로 삼고, 네트워크는 그 로컬 데이터를 갱신하는 선택적 동기화 수단으로 두는** 설계입니다. 핵심은 **UI가 네트워크가 아니라 로컬 DB를 바라본다**는 점입니다.

복원력 관점에서 이 설계가 강력한 이유는, 네트워크 실패가 **사용자 경험의 실패가 아니라 단지 동기화의 지연**이 되기 때문입니다. 네트워크가 끊겨도 로컬 데이터는 그대로 있으므로 앱은 정상 동작합니다.

### 데이터 흐름: 읽기는 로컬에서 {#offline-read-flow}

offline 우선의 읽기 경로는 다음과 같습니다.

1. UI는 **로컬 DB(Room 등)를 관찰**합니다(`Flow<List<T>>`).
2. Repository가 네트워크에서 새 데이터를 받으면 **로컬 DB에 기록**합니다.
3. DB가 갱신되면 1의 Flow가 자동으로 새 값을 방출해 UI가 갱신됩니다.

네트워크 응답이 UI로 직접 가지 않고 **항상 DB를 거친다**는 것이 핵심입니다. 그래서 UI는 데이터 출처가 캐시인지 막 받은 네트워크 응답인지 신경 쓸 필요가 없습니다.

```kotlin
class PostRepository(
    private val dao: PostDao,
    private val api: PostApi,
) {
    // UI는 이 Flow만 본다 — 항상 로컬 DB가 공급원
    fun observePosts(): Flow<List<Post>> = dao.observeAll()

    // 네트워크 결과는 DB에만 쓴다. 실패해도 기존 로컬 데이터는 유지된다.
    suspend fun refresh() {
        runCatching { api.fetchPosts() }
            .onSuccess { dao.upsertAll(it) }     // 성공 시에만 DB 갱신
            // 실패 시 아무것도 하지 않음 → UI는 기존 캐시를 계속 표시
    }
}
```

이 구조에서 `refresh()`가 실패해도 `observePosts()`가 방출하던 데이터는 그대로이므로, **에러가 화면을 비우지 않습니다.** 새로고침 실패는 별도 신호(예: 스낵바)로만 알리면 됩니다.

### 쓰기와 보류된 동기화 {#offline-write-sync}

offline 우선에서 쓰기는 더 까다롭습니다. 사용자가 오프라인 상태에서 글을 작성하면, 그 변경을 **로컬에 먼저 반영하고 동기화는 나중으로 미뤄야** 합니다.

1. 로컬 DB에 변경을 즉시 기록하고, "동기화 대기" 상태로 표시합니다(예: `isSynced = false`).
2. UI는 로컬 DB를 보므로 변경이 즉시 화면에 반영됩니다(낙관적 업데이트).
3. 네트워크가 복구되면 대기 중인 변경을 서버로 전송하고, 성공하면 상태를 "동기화됨"으로 바꿉니다.

이 "나중에 보내기"를 안정적으로 처리하는 표준 도구가 **`WorkManager`**입니다. `WorkManager`는 앱이 종료되거나 기기가 재부팅돼도 작업을 보존하고, 네트워크 제약(`NetworkType.CONNECTED`)이 충족될 때 실행하며, 실패 시 백오프 재시도를 제공합니다. 즉 폴백·재시도·offline 우선이 한 컴포넌트에서 만납니다.

```kotlin
val syncWork = OneTimeWorkRequestBuilder<SyncWorker>()
    .setConstraints(
        Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)   // 연결될 때만 실행
            .build()
    )
    .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 10, TimeUnit.SECONDS)
    .build()

WorkManager.getInstance(context).enqueueUniqueWork(
    "sync_posts",
    ExistingWorkPolicy.KEEP,   // 중복 동기화 방지
    syncWork,
)
```

### 충돌과 정합성에 대한 주의 {#offline-conflict}

offline 우선의 쓰기에서는 **같은 데이터를 로컬과 서버가 서로 다르게 갖는 충돌**이 생길 수 있습니다. 두 기기에서 같은 항목을 오프라인으로 수정한 뒤 둘 다 동기화하는 경우가 그렇습니다. 해소 전략은 작업 성격에 따라 다릅니다.

- **last-write-wins**: 타임스탬프가 늦은 쪽으로 덮어쓰기. 단순하지만 먼저 한 변경이 사라질 수 있습니다.
- **서버 권위**: 서버 값이 항상 우선. 로컬 변경은 충돌 시 폐기·재적용.
- **병합**: 필드 단위로 합치거나 사용자에게 선택을 요청.

복원력 설계에서 offline 우선을 도입할 때는, 읽기 캐시만 할 것인지 쓰기 동기화까지 할 것인지를 먼저 정해야 합니다. **읽기 캐시는 비교적 단순하지만, 쓰기 동기화는 충돌 해소 정책이 반드시 따라옵니다.**

## 요약 {#summary}

> **TL;DR** — 복원력 설계는 실패를 정상 사건으로 전제하고 그 영향을 국소화합니다. (1) `supervisorScope`와 섹션별 상태 모델로 **부분 실패**가 화면 전체로 번지지 않게 격리하고, (2) 일시적 실패는 지수 백오프 **재시도**로 만회하되 멱등한 작업에만 적용하며, 그래도 안 되면 캐시·기본값 **폴백**으로 메웁니다. (3) **offline 우선**은 로컬 DB를 단일 진실 공급원으로 삼아 네트워크 실패를 동기화 지연으로 격하시키고, 보류된 쓰기는 `WorkManager`로 안정적으로 재전송합니다.

1. **부분 실패 허용**: `supervisorScope` + 자식 내부 예외 포착으로 한 작업의 실패를 격리하고, UI 상태를 섹션별 성공/실패로 모델링해 성공한 부분은 그대로 보여 준다.
2. **폴백·재시도**: 일시적 실패는 재시도 가능한 오류에만 지수 백오프 + jitter로 재시도하고(멱등성 전제), 끝내 실패하면 캐시·기본값·대체 경로로 폴백한다.
3. **offline 우선**: UI가 로컬 DB(단일 진실 공급원)를 관찰하고 네트워크는 DB를 갱신하는 동기화 수단으로 둔다. 보류된 쓰기는 `WorkManager`로 네트워크 복구 시 재전송하며, 쓰기 동기화에는 충돌 해소 정책이 따라온다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 대시보드가 3개 API에서 데이터를 받는데, 하나가 실패하면 화면 전체가 에러로 바뀝니다. 어떻게 고치나요?">

전형적인 부분 실패를 전체 실패로 처리하는 문제입니다. 세 호출을 한 묶음(`coroutineScope`)으로 처리하면 자식 하나의 실패가 형제를 취소하고 예외가 위로 던져져 화면 전체가 무너집니다.

먼저 `supervisorScope`로 묶어 자식 실패가 형제·부모로 전파되지 않게 격리합니다. 그리고 각 `async` 내부에서 `runCatching`(또는 `try/catch`)으로 예외를 `Result`로 포착해, await 지점에서 예외가 다시 던져지는 대신 값(성공값 또는 null/기본값)으로 다뤄지게 합니다. 이때 `CancellationException`은 다시 던져 취소 신호를 보존해야 합니다.

마지막으로 UI 상태 모델을 화면 전체의 단일 `Loading/Success/Error`가 아니라 섹션별 성공/실패를 담을 수 있게(예: `user: User?`, `feed: List<Post>`, `ads: Ad?`) 설계합니다. 그러면 성공한 영역은 정상 표시하고 실패한 영역만 자리 표시자나 재시도 버튼으로 처리할 수 있습니다.

</def>
<def title="Q) 네트워크 실패에 재시도를 넣으려는데, 무엇을 주의해야 하나요?">

세 가지를 주의해야 합니다. 첫째, 재시도 가능한 실패만 재시도합니다. 4xx 같은 클라이언트 오류는 요청 자체가 잘못된 것이라 다시 보내도 같은 결과이므로, 5xx·타임아웃·연결 실패 같은 일시적 오류에만 적용합니다.

둘째, 지수 백오프를 씁니다. 실패 직후 즉시·동일 간격으로 반복하면 부하받은 서버를 더 압박합니다. 간격을 점점 늘리고(1초→2초→4초), 다수 클라이언트가 동시에 재시도하는 것을 분산하기 위해 약간의 무작위 지연(jitter)을 더합니다. `delay`는 suspend 함수라 스레드를 막지 않고 취소에도 반응합니다.

셋째, 멱등성입니다. 재시도하는 작업은 여러 번 실행해도 안전(멱등)해야 합니다. GET 조회는 안전하지만 결제·주문 생성 같은 쓰기는 중복 실행을 일으킬 수 있어, 서버가 멱등성 키로 중복을 무시하도록 설계돼 있어야만 안전하게 재시도할 수 있습니다.

</def>
<def title="Q) 폴백과 재시도는 어떻게 다른가요? 둘을 어떻게 결합하나요?">

재시도는 "같은 작업을 다시 시도"해 일시적 실패를 만회하는 전략이고, 폴백은 "다른 대체 결과로 대신"하는 전략입니다. 재시도는 다시 하면 성공할 가능성이 있는 일시적 오류에 쓰고, 폴백은 그래도 실패가 확정됐을 때 의미 있는 결과를 주기 위해 씁니다.

실무에서는 단계로 결합합니다. 먼저 지수 백오프 재시도로 일시적 실패를 만회하고, 끝내 실패하면 폴백으로 메웁니다. 폴백 원천은 직전 성공값 캐시, 기본값/빈 값, 대체 엔드포인트 등이 있습니다. 코드로는 `runCatching { retryWithBackoff { ... } }.recoverCatching { 캐시 }.getOrDefault(기본값)` 형태가 됩니다. 폴백으로 오래된 캐시를 보여 줄 때는 사용자가 최신 데이터로 오해하지 않게 "오프라인 데이터" 같은 표시를 함께 두는 편이 정확합니다.

</def>
<def title="Q) offline 우선(offline-first) 설계가 무엇이고, 왜 복원력에 강한가요?">

offline 우선은 로컬 저장소(Room 등)를 단일 진실 공급원으로 삼고, 네트워크는 그 로컬 데이터를 갱신하는 선택적 동기화 수단으로 두는 설계입니다. 핵심은 UI가 네트워크가 아니라 로컬 DB를 관찰한다는 점입니다.

읽기 경로는 UI가 DB의 Flow를 구독하고, Repository가 네트워크 응답을 직접 UI로 보내지 않고 항상 DB에 먼저 기록하는 식입니다. DB가 갱신되면 Flow가 새 값을 방출해 UI가 갱신됩니다. 이 구조에서 새로고침이 실패해도 DB의 기존 데이터는 그대로이므로 화면이 비지 않습니다. 즉 네트워크 실패가 사용자 경험의 실패가 아니라 단지 동기화의 지연이 됩니다. 이것이 복원력에 강한 이유입니다.

</def>
<def title="Q) offline 상태에서 사용자가 쓴 데이터를 어떻게 처리하나요?">

쓰기는 로컬에 먼저 반영하고 동기화를 미루는 방식으로 처리합니다. 먼저 로컬 DB에 변경을 즉시 기록하면서 "동기화 대기"로 표시하고(예: `isSynced = false`), UI는 DB를 보므로 변경이 즉시 화면에 반영됩니다(낙관적 업데이트). 네트워크가 복구되면 대기 중인 변경을 서버로 전송하고 성공 시 상태를 "동기화됨"으로 바꿉니다.

이 보류된 동기화를 안정적으로 처리하는 표준 도구가 `WorkManager`입니다. 앱 종료·재부팅에도 작업을 보존하고, `NetworkType.CONNECTED` 제약으로 연결될 때만 실행하며, 백오프 재시도를 제공합니다. 한 가지 더 고려할 점은 충돌입니다. 여러 기기가 같은 항목을 오프라인으로 수정한 뒤 동기화하면 충돌이 생기므로, last-write-wins·서버 권위·필드 병합 같은 해소 정책을 작업 성격에 맞게 정해야 합니다.

</def>
</deflist>
