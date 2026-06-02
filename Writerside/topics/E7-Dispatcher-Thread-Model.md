# E7) Dispatcher와 스레드 모델

## CoroutineDispatcher란 {#dispatcher-basics}

`CoroutineDispatcher`는 **코루틴이 어떤 스레드(또는 스레드 풀)에서 실행되고 재개될지를 결정하는** `CoroutineContext`의 요소입니다. 코루틴은 자기 자신이 스레드를 고르지 않습니다. 스코프의 컨텍스트에 들어 있는 디스패처가 그 코루틴의 본문 실행과, suspend 후 재개 시점에 실행을 어느 스레드로 보낼지를 정합니다.

여기서 정확히 구분해야 할 두 개념이 있습니다.

- **코루틴(coroutine)**: 일시 중단 가능한 작업 단위. 스레드가 아닙니다.
- **디스패처(dispatcher)**: 그 작업을 실제 스레드에 배치(dispatch)하는 주체.

따라서 코루틴 하나가 여러 스레드를 거쳐 실행될 수 있습니다. suspend 지점 이전은 스레드 A에서, 재개 후는 스레드 B에서 돌 수 있고, 그 전환을 디스패처가 관리합니다.

```kotlin
// 디스패처는 컨텍스트의 한 요소다
val scope = CoroutineScope(Job() + Dispatchers.IO)

scope.launch {
    // 이 본문은 Dispatchers.IO가 관리하는 스레드 풀에서 실행된다
}
```

## Main · IO · Default {#main-io-default}

`Dispatchers`는 코틀린 코루틴이 제공하는 표준 디스패처들의 모음입니다. 안드로이드에서 실무상 거의 전부를 차지하는 세 개를 정확히 구분하는 것이 핵심입니다.

### Dispatchers.Main {#dispatcher-main}

UI 스레드(안드로이드의 메인 스레드) 하나에서만 코루틴을 실행하는 디스패처입니다. UI 갱신, `View`·`LiveData`·Compose 상태 접근처럼 **메인 스레드에서만 해야 하는 작업**에 씁니다.

- 안드로이드에서 `Dispatchers.Main`은 내부적으로 메인 스레드의 `Handler`(메인 `Looper`)에 작업을 게시(post)하는 방식으로 동작합니다.
- 이 구현체는 `kotlinx-coroutines-android` 아티팩트가 클래스패스에 있어야 제공됩니다. 없으면 런타임에 "Module with the Main dispatcher is missing" 예외가 납니다.
- `Dispatchers.Main.immediate`는 이미 메인 스레드에 있으면 재게시(re-dispatch) 없이 즉시 실행해, 불필요한 한 프레임 지연을 피합니다.

### Dispatchers.IO {#dispatcher-io}

**블로킹 I/O 작업**을 위한 디스패처입니다. 네트워크 요청, 파일 읽기/쓰기, 데이터베이스 쿼리처럼 스레드가 결과를 기다리며 블로킹되는 작업에 씁니다.

- 기본적으로 **최대 64개**(또는 코어 수가 그보다 많으면 코어 수)까지 스레드를 사용하도록 제한됩니다. 블로킹 작업은 스레드를 점유한 채 대기하므로, 동시 블로킹 작업이 많아도 견디도록 풀이 넉넉합니다.
- `Dispatchers.IO`와 `Dispatchers.Default`는 **같은 스레드 풀을 공유**합니다. 별개의 풀이 아니라, 공용 풀에서 각자 다른 동시 실행 한도(parallelism limit)를 가질 뿐입니다. 그래서 `IO`에서 `Default`로 `withContext` 전환할 때 같은 스레드가 재사용되어 실제 스레드 교체가 일어나지 않을 수도 있습니다.

### Dispatchers.Default {#dispatcher-default}

**CPU 집약적 연산**을 위한 디스패처입니다. 큰 리스트 정렬·필터링, JSON 파싱, 이미지 디코딩, 복잡한 계산 등 CPU를 오래 쓰는 작업에 씁니다.

- 동시 실행 스레드 수가 **CPU 코어 수**(최소 2)로 제한됩니다. CPU 바운드 작업은 코어 수보다 많은 스레드를 돌려도 컨텍스트 스위칭 비용만 늘고 처리량이 늘지 않기 때문입니다.
- 코루틴 빌더에 디스패처를 명시하지 않고 스코프 컨텍스트에도 디스패처가 없으면 `Dispatchers.Default`가 쓰입니다(`GlobalScope` 등). 단, `viewModelScope`처럼 `Dispatchers.Main.immediate`를 기본으로 가진 스코프는 예외입니다.

### IO와 Default를 나눠 쓰는 이유 {#why-split-io-default}

둘을 구분하는 근거는 **스레드 점유 특성이 다르기 때문**입니다. IO 작업은 스레드를 점유한 채 외부 응답을 기다리므로(블로킹), 동시 작업 수만큼 스레드가 필요해 한도가 큽니다. CPU 작업은 스레드가 실제로 코어를 계속 돌리므로, 코어 수를 넘는 동시성은 오히려 손해라 한도가 코어 수로 작습니다. 같은 풀을 공유하되 한도를 다르게 두는 설계가 이 차이를 흡수합니다.

| 디스패처 | 용도 | 동시 실행 한도 | 대표 작업 |
|----------|------|----------------|-----------|
| Main | UI 접근 | 메인 스레드 1개 | View/Compose 상태 갱신 |
| IO | 블로킹 I/O | 기본 64개(코어 수 이상) | 네트워크, 파일, DB |
| Default | CPU 연산 | 코어 수(최소 2) | 정렬, 파싱, 디코딩 |

## withContext로 디스패처 전환하기 {#with-context}

`withContext(context)`는 **현재 코루틴의 컨텍스트를 일시적으로 바꿔 블록을 실행하고, 그 결과를 반환한 뒤 원래 컨텍스트로 돌아오는** suspend 함수입니다. 디스패처 전환의 표준 도구입니다.

```kotlin
class UserRepository(
    private val api: Api,
    private val dao: UserDao,
) {
    // 호출자는 어느 스레드에서 호출해도 된다 — 내부에서 스스로 전환한다
    suspend fun loadUser(id: String): User = withContext(Dispatchers.IO) {
        val dto = api.fetchUser(id)   // 블로킹 네트워크 → IO에서
        dao.insert(dto)               // 블로킹 DB → IO에서
        dto.toUser()
    }
}
```

### withContext의 동작과 성질 {#with-context-semantics}

- **순차적입니다.** `withContext`는 새 코루틴을 동시에 띄우는 것이 아니라, 현재 코루틴을 지정 디스패처로 옮겨 블록을 실행하고 끝날 때까지 일시 중단합니다. 병렬이 아니라 "스레드 전환 후 그 자리에서 계속"입니다.
- **블록의 마지막 표현식을 결과로 반환합니다.** `async`/`await` 없이 값을 받을 수 있습니다.
- **구조적 동시성을 유지합니다.** 호출한 코루틴의 자식으로 동작하므로, 호출 코루틴이 취소되면 `withContext` 블록도 함께 취소됩니다.

### launch(Dispatcher)와의 차이 {#with-context-vs-launch}

`launch(Dispatchers.IO) { ... }`는 새 자식 코루틴을 그 디스패처에서 **동시에 시작**하고 `Job`을 반환합니다. 반면 `withContext`는 새 코루틴을 만들지 않고 **현재 코루틴을 옮겨** 결과를 돌려줍니다. "지금 이 흐름을 다른 스레드에서 이어서 처리하고 결과를 받고 싶다"면 `withContext`, "별도 작업을 띄워 두고 흐름을 계속하고 싶다"면 `launch`입니다.

### 흔한 안티패턴: 호출자에게 전환을 떠넘기기 {#with-context-antipattern}

`suspend` 함수는 **자신이 어느 디스패처를 필요로 하는지 스스로 책임지는 것**이 권장됩니다(이를 main-safety라 부릅니다). 즉 위 `loadUser`처럼 함수 내부에서 `withContext(Dispatchers.IO)`로 감싸면, 호출자는 메인 스레드에서 그냥 호출해도 안전합니다.

```kotlin
// 권장: 함수가 스스로 전환을 책임진다 (main-safe)
suspend fun loadUser(): User = withContext(Dispatchers.IO) { /* ... */ }

// 비권장: 호출자가 매번 감싸야 한다 — 잊으면 메인 스레드 블로킹
viewModelScope.launch(Dispatchers.IO) {  // 호출 측에 전환 책임이 샌다
    val user = repository.loadUserNotMainSafe()
    withContext(Dispatchers.Main) { render(user) }  // 매번 반복
}
```

## 스레드 풀과 수명 관리 {#thread-pool}

표준 디스패처가 스레드를 어떻게 관리하는지 정확히 알아야 잘못된 사용을 피할 수 있습니다.

### 공용 풀과 한도 {#shared-pool-limits}

앞서 본 대로 `Dispatchers.Default`와 `Dispatchers.IO`는 동일한 공용 스레드 풀(`kotlinx.coroutines`의 기본 스케줄러) 위에서 동작합니다. 두 디스패처는 그 풀에서 **서로 다른 동시 실행 한도**만 적용받습니다.

- `Default`: 코어 수만큼만 동시에 CPU를 점유하도록 제한.
- `IO`: 블로킹 대기를 견디기 위해 기본 64개까지 동시 실행 허용.

이 풀의 스레드는 데몬 스레드라 작업이 없으면 유휴 상태로 대기하며, 앱이 종료될 때 별도 정리 없이 사라집니다.

### limitedParallelism으로 한도 좁히기 {#limited-parallelism}

같은 풀을 공유하면서도 특정 작업의 동시 실행 수를 제한하고 싶으면 `limitedParallelism(n)`을 씁니다. 새 스레드를 만들지 않고, 공용 풀 위에서 **동시 실행 수만 n으로 제한한 뷰(view)**를 돌려줍니다.

```kotlin
// 한 번에 1개만 실행되는 IO 디스패처 뷰 — 별도 스레드 생성 없음
private val singleThreadIo = Dispatchers.IO.limitedParallelism(1)
```

이는 직접 만든 `newSingleThreadContext`보다 권장됩니다. 후자는 전용 스레드를 새로 만들고 `close()`로 직접 해제해야 하므로 누수 위험이 있습니다.

### 직접 만든 풀 닫기 {#close-custom-pool}

`Executors`로 만든 스레드 풀을 디스패처로 쓸 수도 있습니다. 이 경우 **수명 관리 책임이 사용자에게 있습니다.** 더 이상 쓰지 않으면 `close()`로 풀을 해제해야 스레드가 누수되지 않습니다.

```kotlin
val pool = Executors.newFixedThreadPool(4).asCoroutineDispatcher()
try {
    withContext(pool) { /* ... */ }
} finally {
    pool.close()   // 직접 만든 풀은 직접 닫아야 한다
}
```

## 디스패처를 주입 가능하게 만들기 {#injectable-dispatchers}

코드에서 `Dispatchers.IO`, `Dispatchers.Main`을 **직접 하드코딩하면 테스트가 어려워집니다.** 단위 테스트에서는 디스패처를 테스트용으로 바꿔 끼울 수 있어야 합니다. 그래서 디스패처를 의존성으로 주입(inject) 가능하게 설계하는 것이 권장됩니다.

### 왜 하드코딩이 문제인가 {#why-not-hardcode}

- 테스트 환경에는 안드로이드 메인 `Looper`가 없어 `Dispatchers.Main`이 동작하지 않습니다. `kotlinx-coroutines-test`의 `StandardTestDispatcher`/`UnconfinedTestDispatcher`로 교체해야 합니다.
- 가상 시간(virtual time) 제어로 `delay` 등을 즉시 진행시키려면, 테스트 디스패처를 실제 코드에 주입할 수 있어야 합니다.
- `Dispatchers.IO`/`Default`의 실제 스레드 스케줄링은 테스트를 비결정적으로 만들 수 있습니다. 단일 테스트 디스패처로 통일하면 실행 순서가 결정적이 됩니다.

### DispatcherProvider 패턴 {#dispatcher-provider}

디스패처들을 인터페이스로 추상화해 주입합니다. 운영 코드에는 실제 `Dispatchers`를, 테스트에는 테스트 디스패처를 넣습니다.

```kotlin
interface DispatcherProvider {
    val main: CoroutineDispatcher
    val io: CoroutineDispatcher
    val default: CoroutineDispatcher
}

class DefaultDispatcherProvider : DispatcherProvider {
    override val main = Dispatchers.Main
    override val io = Dispatchers.IO
    override val default = Dispatchers.Default
}
```

```kotlin
class UserRepository(
    private val api: Api,
    private val dispatchers: DispatcherProvider,
) {
    suspend fun loadUser(id: String): User =
        withContext(dispatchers.io) { api.fetchUser(id).toUser() }
}
```

### Hilt로 주입하기 {#hilt-qualifier}

Hilt에서는 같은 타입(`CoroutineDispatcher`)을 여러 개 주입해야 하므로, **한정자(qualifier)**로 구분합니다. 같은 타입을 한정자 없이 여러 번 바인딩하면 어느 것을 주입할지 모호해 컴파일이 실패하기 때문입니다.

```kotlin
@Retention(AnnotationRetention.BINARY)
@Qualifier
annotation class IoDispatcher

@Module
@InstallIn(SingletonComponent::class)
object DispatcherModule {
    @IoDispatcher
    @Provides
    fun provideIoDispatcher(): CoroutineDispatcher = Dispatchers.IO
}
```

```kotlin
class UserRepository @Inject constructor(
    private val api: Api,
    @IoDispatcher private val ioDispatcher: CoroutineDispatcher,
) {
    suspend fun loadUser(id: String): User =
        withContext(ioDispatcher) { api.fetchUser(id).toUser() }
}
```

테스트에서는 이 모듈을 `TestInstallIn`으로 교체하거나, 생성자에 직접 테스트 디스패처를 넘겨 실제 스레드 풀 없이 결정적으로 검증할 수 있습니다.

## 요약 {#summary}

> **TL;DR** — 디스패처는 코루틴이 어느 스레드에서 실행될지를 정합니다. UI는 `Main`, 블로킹 I/O는 `IO`(기본 64), CPU 연산은 `Default`(코어 수)이며 IO와 Default는 같은 풀을 한도만 달리해 공유합니다. 디스패처 전환은 새 코루틴을 띄우는 게 아니라 현재 흐름을 옮기는 `withContext`로 하고, 함수가 스스로 전환을 책임지면(main-safety) 호출자가 안전합니다. 디스패처를 하드코딩하지 말고 `DispatcherProvider`나 Hilt 한정자로 주입해 테스트 가능하게 만듭니다.

1. **Main · IO · Default**: Main은 UI 스레드 전용, IO는 블로킹 I/O용(기본 64개), Default는 CPU 연산용(코어 수). IO와 Default는 같은 풀을 동시 실행 한도만 달리해 공유한다.
2. **withContext**: 새 코루틴을 띄우지 않고 현재 코루틴을 지정 디스패처로 옮겨 블록을 실행하고 결과를 반환한다. 순차적이며 구조적 동시성을 유지한다. 함수가 스스로 전환을 책임지는 main-safety가 권장된다.
3. **스레드 풀**: Default/IO는 공용 풀을 공유하고 한도만 다르다. 좁히려면 `limitedParallelism`, 직접 만든 풀은 `close()`로 직접 해제한다.
4. **주입 가능화**: `Dispatchers`를 하드코딩하면 테스트가 어렵다. `DispatcherProvider` 인터페이스나 Hilt 한정자로 주입해, 테스트에서 테스트 디스패처로 교체한다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Dispatchers.IO와 Dispatchers.Default는 무엇이 다르고, 왜 동시 실행 한도가 다른가요?">

`Dispatchers.IO`는 네트워크·파일·DB처럼 스레드가 결과를 기다리며 블로킹되는 I/O 작업용이고, `Dispatchers.Default`는 정렬·파싱·디코딩처럼 CPU를 계속 점유하는 연산용입니다.

한도가 다른 이유는 스레드 점유 특성 때문입니다. IO 작업은 스레드를 잡은 채 외부 응답을 기다리므로 동시 작업 수만큼 스레드가 필요해 기본 64개(코어 수가 더 많으면 코어 수)까지 허용합니다. CPU 작업은 스레드가 실제로 코어를 돌리므로 코어 수보다 많은 동시성은 컨텍스트 스위칭 비용만 늘려 손해라, 코어 수(최소 2)로 제한합니다. 두 디스패처는 사실 같은 공용 스레드 풀을 공유하며, 이 동시 실행 한도만 다르게 적용받습니다.

</def>
<def title="Q) withContext와 launch(dispatcher)는 어떻게 다른가요?">

`withContext(dispatcher)`는 새 코루틴을 만들지 않고 현재 코루틴을 지정 디스패처로 옮겨 블록을 실행한 뒤, 결과를 반환하고 원래 컨텍스트로 돌아옵니다. 순차적이며 블록의 마지막 표현식이 반환값이 됩니다.

`launch(dispatcher)`는 새 자식 코루틴을 그 디스패처에서 동시에 시작하고 `Job`을 반환합니다. 즉 호출 흐름과 별개로 작업이 병렬로 진행됩니다. "지금 이 흐름을 다른 스레드에서 이어서 처리하고 결과를 받고 싶다"면 `withContext`, "별도 작업을 띄워 두고 현재 흐름을 계속하고 싶다"면 `launch`입니다. 단순한 스레드 전환에 `async { ... }.await()`를 쓰는 것은 불필요한 코루틴을 만드는 것이므로 `withContext`가 더 적절합니다.

</def>
<def title="Q) main-safety란 무엇이고 왜 suspend 함수가 스스로 디스패처를 책임져야 하나요?">

main-safety란 suspend 함수를 메인 스레드에서 호출해도 메인 스레드를 블로킹하지 않도록 보장하는 성질입니다. 함수 내부에서 필요한 디스패처로 `withContext` 전환을 직접 수행하면, 호출자는 어느 스레드에서 호출하든 안전합니다.

함수가 스스로 책임지지 않고 전환을 호출자에게 떠넘기면, 모든 호출 지점이 매번 올바른 디스패처로 감싸야 합니다. 한 곳이라도 빠뜨리면 블로킹 작업이 메인 스레드에서 돌아 ANR이나 프레임 드랍을 유발합니다. 전환 책임을 함수 안에 캡슐화하면 이런 실수의 여지가 사라지고 호출부가 단순해집니다.

</def>
<def title="Q) 코드에서 Dispatchers.IO를 직접 쓰면 어떤 문제가 있고, 어떻게 주입 가능하게 만드나요?">

`Dispatchers.IO`나 `Dispatchers.Main`을 직접 하드코딩하면 테스트가 어려워집니다. 테스트 환경에는 안드로이드 메인 Looper가 없어 `Dispatchers.Main`이 동작하지 않고, 실제 스레드 스케줄링은 테스트를 비결정적으로 만들며, `delay` 등을 가상 시간으로 즉시 진행시킬 수도 없습니다.

해결책은 디스패처를 의존성으로 주입하는 것입니다. `DispatcherProvider` 인터페이스로 main/io/default를 추상화해, 운영 코드에는 실제 `Dispatchers`를, 테스트에는 `kotlinx-coroutines-test`의 테스트 디스패처를 주입합니다. Hilt를 쓴다면 같은 `CoroutineDispatcher` 타입을 여러 개 구분하기 위해 `@IoDispatcher` 같은 한정자(qualifier)를 만들어 바인딩합니다. 그러면 테스트에서 단일 테스트 디스패처로 교체해 실행 순서를 결정적으로 만들 수 있습니다.

</def>
<def title="Q) 안드로이드에서 Dispatchers.Main은 내부적으로 어떻게 동작하나요?">

안드로이드에서 `Dispatchers.Main`은 메인 스레드의 `Handler`(메인 `Looper`)에 작업을 게시하는 방식으로 동작합니다. 코루틴이 메인 디스패처로 재개될 때, 그 재개 작업이 메인 스레드의 메시지 큐에 올라가 차례가 되면 실행됩니다.

이 구현체는 `kotlinx-coroutines-android` 아티팩트가 클래스패스에 있어야 제공되며, 없으면 런타임에 메인 디스패처 모듈이 없다는 예외가 발생합니다. 또한 `Dispatchers.Main.immediate`는 호출 시점에 이미 메인 스레드에 있다면 재게시 없이 즉시 실행해, 큐를 한 바퀴 도는 불필요한 지연을 줄입니다. `viewModelScope`가 기본 디스패처로 `Dispatchers.Main.immediate`를 쓰는 이유가 이 즉시성 때문입니다.

</def>
</deflist>
