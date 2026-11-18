# Q35) 코루틴 컨텍스트

코루틴 컨텍스트는 코루틴을 실행하는 데 필요한 설정을 모아 둔 묶음입니다. 어느 스레드에서 실행할지, 누가 부모인지, 이름이 무엇인지, 잡히지 않은 예외를 어디로 보낼지가 모두 이 묶음에 들어 있습니다.

Q34의 [코루틴 컨텍스트 미리 보기](Q34-coroutine-builder.md#context-preview)에서 요소를 `+`로 합치고 `[키]`로 꺼내는 법, 빌더가 부모 컨텍스트를 이어받는 법을 봤습니다. 이 토픽에서는 그 다음을 봅니다. 요소를 꺼낼 때 쓰는 "키"가 정확히 무엇인지, 대표 요소 네 가지가 각각 무엇을 정하는지, 컨텍스트가 왜 바꿀 수 없게(불변으로) 만들어졌는지, `ThreadLocal`과 무엇이 다른지, 요소를 직접 만들어 쓰는 법, 그리고 컨텍스트를 읽는 두 가지 방법의 차이입니다. `plus`·`fold`·`minusKey`가 안에서 어떻게 동작하는지는 [CoroutineContext 인터페이스](Details-CoroutineContext-인터페이스.md)에서 따로 다룹니다.

예제는 Kotlin 2.4.21, kotlinx-coroutines 1.11.0, JDK 25에서 실행했습니다. 라이브러리 내부 코드도 같은 버전의 소스에서 옮겼습니다.

## 키로 찾는 요소 묶음 {#indexed-set}

코루틴 컨텍스트는 맵과 집합을 섞은 구조입니다. 맵처럼 키로 요소를 꺼내고, 집합처럼 같은 키의 요소는 하나만 들어갑니다. 코틀린 코루틴 설계 문서(KEEP)는 이것을 "인덱싱된 집합(indexed set)"이라고 부릅니다.

여기서 키는 문자열이 아니라 **요소 클래스의 `companion object`** 입니다. `CoroutineName`의 소스를 보면 이렇게 되어 있습니다.

```kotlin
// CoroutineName.kt (kotlinx-coroutines 1.11.0)
public data class CoroutineName(
    val name: String
) : AbstractCoroutineContextElement(CoroutineName) {
    public companion object Key : CoroutineContext.Key<CoroutineName>

    override fun toString(): String = "CoroutineName($name)"
}
```

- `companion object Key`가 키입니다. 코틀린에서 클래스 이름만 쓰면 그 클래스의 `companion object`를 가리키므로, `context[CoroutineName]`의 `CoroutineName`은 클래스가 아니라 이 `Key` 객체입니다.
- 상위 클래스 생성자에 넘긴 `CoroutineName`도 같은 `Key` 객체입니다. "내 키는 이것"이라고 등록하는 부분입니다.
- `Key`에 타입 인자 `<CoroutineName>`이 붙어 있어서, `context[CoroutineName]`의 결과 타입이 `CoroutineName?`으로 정해집니다. 꺼낸 뒤 형변환할 필요가 없습니다.

요소 하나도 그 자체로 컨텍스트입니다. `CoroutineContext.Element`가 `CoroutineContext`를 상속하기 때문에, 요소 하나를 "요소가 하나뿐인 컨텍스트"로 그대로 쓸 수 있습니다. `launch(CoroutineName("다운로드"))`처럼 요소를 컨텍스트 자리에 바로 넘길 수 있는 이유입니다.

```kotlin
// ElementKey.kt
import kotlinx.coroutines.*
import kotlin.coroutines.ContinuationInterceptor
import kotlin.coroutines.CoroutineContext

fun main() {
    val name = CoroutineName("다운로드")

    // 1. 요소 하나도 그 자체로 컨텍스트입니다
    val single: CoroutineContext = name
    println("1) ${single[CoroutineName]}")

    // 2. 요소의 키는 그 클래스의 companion object 입니다
    println("2) ${name.key === CoroutineName}")

    // 3. 디스패처의 키는 ContinuationInterceptor 입니다
    val context = name + Dispatchers.IO + Job()
    println("3) ${Dispatchers.IO.key === ContinuationInterceptor}")
    println("   ${context[ContinuationInterceptor]}")

    // 4. 키로 꺼낸 값은 타입이 정해져 있어 형변환이 필요 없습니다
    val job: Job? = context[Job]
    println("4) ${job?.isActive}")
}
```

```text
1) CoroutineName(다운로드)
2) true
3) true
   Dispatchers.IO
4) true
```

3)이 눈여겨볼 부분입니다. 디스패처의 키는 `CoroutineDispatcher`가 아니라 `ContinuationInterceptor`입니다. Q32에서 본 것처럼 일시 중단된 코루틴은 `Continuation`의 `resumeWith`로 재개되는데, `ContinuationInterceptor`는 이 재개를 가로채서 다른 스레드로 넘길 수 있는 요소입니다. 디스패처는 이 인터셉터의 한 종류이고, 그래서 디스패처끼리는 모두 같은 키를 씁니다. `Dispatchers.Main + Dispatchers.IO`를 하면 둘이 함께 들어가지 않고 뒤의 `IO`만 남습니다.

`context[CoroutineDispatcher]`처럼 쓰는 코드도 보이는데, kotlinx-coroutines 1.11부터 경고가 나오는 폐기 예정 API입니다. 디스패처가 필요하면 `context[ContinuationInterceptor] as? CoroutineDispatcher`로 꺼냅니다.

## Job {#job}

`Job`은 코루틴의 상태(실행 중, 완료, 취소)와 부모·자식 관계를 담는 요소입니다. 자세한 동작은 Q36에서 다루고, 여기서는 컨텍스트 요소로서의 특징만 봅니다.

다른 요소는 부모에게서 그대로 물려받지만 `Job`은 그렇지 않습니다. 빌더는 코루틴을 만들 때마다 그 코루틴 객체 자신을 새 `Job`으로 넣고, 물려받은 `Job`은 부모로 연결만 합니다([컨텍스트 합치기](Q34-coroutine-builder.md#new-context)). 그래서 코루틴 안에서 `coroutineContext[Job]`을 읽으면 항상 지금 실행 중인 그 코루틴이 나옵니다.

`CoroutineScope(context)` 함수도 `Job`을 챙깁니다. 넘긴 컨텍스트에 `Job`이 없으면 `Job()`을 새로 만들어 붙입니다.

```kotlin
// CoroutineScope.kt (kotlinx-coroutines 1.11.0)
public fun CoroutineScope(context: CoroutineContext): CoroutineScope =
    ContextScope(if (context[Job] != null) context else context + Job())
```

스코프에 `Job`이 있어야 그 스코프에서 시작한 코루틴들이 같은 부모 아래 묶이고, `scope.cancel()` 한 번으로 모두 취소할 수 있기 때문입니다.

빌더에 `Job`을 직접 넘기는 것(`launch(Job()) { }`)은 피합니다. 넘긴 `Job`이 새 코루틴의 부모가 되면서 원래 부모와의 연결이 끊깁니다. 어떤 일이 생기는지는 Q36에서 실행으로 확인합니다.

## 디스패처 {#dispatcher}

디스패처(`CoroutineDispatcher`)는 코루틴을 어느 스레드에서 실행할지 정합니다. 처음 시작할 때뿐 아니라 일시 중단됐다가 재개될 때마다 디스패처가 실행할 스레드를 고릅니다. 종류별 내부 구조는 Q38에서 다루고, 여기서는 네 가지의 용도만 정리합니다.

| 디스패처 | 실행하는 곳 | 쓰는 곳 |
|---|---|---|
| `Dispatchers.Main` | UI 스레드 하나 | 화면 갱신. 안드로이드·스윙처럼 UI 스레드가 있는 환경에서만 있습니다 |
| `Dispatchers.Default` | CPU 코어 수만큼의 스레드 풀 (최소 2개) | 정렬, JSON 파싱처럼 CPU를 계속 쓰는 계산 |
| `Dispatchers.IO` | 필요하면 늘어나는 스레드 풀 (기본 최대 64개, 코어가 더 많으면 코어 수) | 파일, 네트워크, DB처럼 기다리는 시간이 긴 작업 |
| `Dispatchers.Unconfined` | 정해진 스레드 없음 | 테스트나 특수한 경우. 일반 코드에서는 거의 쓰지 않습니다 |

`Unconfined`는 동작이 직관과 달라서 실행으로 확인해 봤습니다.

```kotlin
// Unconfined.kt
import kotlinx.coroutines.*

fun threadName(): String = Thread.currentThread().name

fun main() = runBlocking<Unit> {
    launch(Dispatchers.Unconfined) {
        println("1) 시작: ${threadName()}")
        delay(100)   // delay 는 내부 타이머 스레드에서 재개시킵니다
        println("2) 재개: ${threadName()}")
    }
}
```

```text
1) 시작: main
2) 재개: kotlinx.coroutines.DefaultExecutor
```

`Unconfined`는 처음에 `launch`를 부른 스레드(`main`)에서 바로 실행되고, 재개될 때는 **재개시킨 쪽의 스레드**에서 이어서 실행됩니다. `delay`는 시간이 되면 내부 타이머 스레드(`DefaultExecutor`)에서 코루틴을 재개시키므로, 그 뒤 코드는 타이머 스레드에서 실행되었습니다. 재개 후의 스레드를 알맞게 골라 주는 것이 아니라, 어느 스레드가 될지 정하지 않는다는 뜻입니다.

## CoroutineName {#coroutine-name}

`CoroutineName`은 코루틴에 이름을 붙이는 요소입니다. 실행 동작에는 영향을 주지 않고, 디버깅할 때 어느 코루틴인지 알아보는 데만 씁니다.

이름은 디버그 모드에서 스레드 이름에 붙어서 보입니다. 디버그 모드는 JVM 옵션 `-Dkotlinx.coroutines.debug`를 주거나, `-ea`로 assertion을 켜면 켜집니다.

```kotlin
// DebugName.kt  (-Dkotlinx.coroutines.debug 로 실행)
import kotlinx.coroutines.*

fun threadName(): String = Thread.currentThread().name

fun main() = runBlocking<Unit> {
    launch(CoroutineName("다운로드")) {
        println("1) ${threadName()}")
    }
    launch {
        println("2) ${threadName()}")
    }
}
```

```text
1) main @다운로드#2
2) main @coroutine#3
```

- `@` 뒤가 코루틴 이름, `#` 뒤가 코루틴 번호입니다. `runBlocking`이 1번이라 두 `launch`는 2번, 3번이 되었습니다.
- 이름이 없으면 `coroutine`이 들어갑니다.
- 스레드 이름은 코루틴이 그 스레드에서 실행되는 동안에만 바뀌고, 일시 중단되면 원래 이름으로 돌아갑니다. 디버그 모드에서 빌더가 넣는 `CoroutineId` 요소가 이 일을 합니다. 로그에 스레드 이름을 찍어 두면 어느 코루틴이 남긴 로그인지 바로 구분됩니다.

## CoroutineExceptionHandler {#exception-handler}

`CoroutineExceptionHandler`는 코루틴 안에서 잡히지 않은 예외를 받는 요소입니다. 예외 처리 전체는 Q41에서 다루고, 여기서는 컨텍스트 요소로서 알아 둘 점 하나만 봅니다. **이 요소를 넣어도 쓰이지 않는 자리가 있습니다.**

```kotlin
// HandlerRoot.kt
import kotlinx.coroutines.*

fun main() = runBlocking<Unit> {
    val rootHandler = CoroutineExceptionHandler { _, e -> println("루트 핸들러가 받음: ${e.message}") }
    val childHandler = CoroutineExceptionHandler { _, e -> println("자식 핸들러가 받음: ${e.message}") }

    // 부모가 없는 스코프에서 시작한 코루틴(루트)이 예외 처리를 맡습니다
    val scope = CoroutineScope(Dispatchers.Default + rootHandler)
    val root = scope.launch {
        // 자식에 붙인 핸들러는 쓰이지 않습니다. 예외는 부모로 올라갑니다
        launch(childHandler) {
            throw IllegalStateException("자식 실패")
        }
    }
    root.join()
}
```

```text
루트 핸들러가 받음: 자식 실패
```

자식 코루틴은 예외가 나면 자기가 처리하지 않고 부모에게 넘깁니다. 예외는 부모를 따라 맨 위의 코루틴까지 올라가고, 거기서 그 코루틴의 컨텍스트에 있는 핸들러가 불립니다. 그래서 자식에게 붙인 `childHandler`는 불리지 않았습니다. 핸들러는 스코프를 만들 때나 맨 위의 `launch`에 넣어야 합니다.

## 불변 컨텍스트와 withContext {#immutability}

컨텍스트는 한 번 만들면 바꿀 수 없습니다. `+`나 `minusKey`는 원래 컨텍스트를 고치지 않고 새 컨텍스트를 만들어 돌려줍니다.

```kotlin
// Immutable.kt
import kotlinx.coroutines.*

fun main() = runBlocking<Unit> {
    // 1. + 는 기존 컨텍스트를 바꾸지 않고 새 컨텍스트를 만듭니다
    val base = CoroutineName("기본")
    val added = base + Dispatchers.IO
    println("1) base=$base, added=$added")

    // 2. withContext 는 블록 동안만 다른 컨텍스트로 실행합니다
    launch(CoroutineName("화면")) {
        println("2) 앞: ${currentCoroutineContext()[CoroutineName]?.name}")
        withContext(CoroutineName("저장")) {
            println("3) 블록 안: ${currentCoroutineContext()[CoroutineName]?.name}")
        }
        println("4) 뒤: ${currentCoroutineContext()[CoroutineName]?.name}")
    }
}
```

```text
1) base=CoroutineName(기본), added=[CoroutineName(기본), Dispatchers.IO]
2) 앞: 화면
3) 블록 안: 저장
4) 뒤: 화면
```

불변으로 만든 이유는 컨텍스트가 여러 코루틴에 공유되기 때문입니다. 부모 컨텍스트는 자식 수십 개가 함께 참조하고, 그 자식들은 서로 다른 스레드에서 실행될 수 있습니다. 누군가 컨텍스트를 고칠 수 있다면 다른 코루틴의 설정까지 몰래 바뀌고, 여러 스레드가 동시에 읽고 쓰는 문제도 막아야 합니다. 바꿀 수 없게 해 두면 잠금 없이 마음 놓고 공유할 수 있습니다.

설정을 바꾸고 싶으면 바꾼 컨텍스트로 새로 실행합니다. 새 코루틴을 시작하거나(`launch(Dispatchers.IO) { }`), 지금 코루틴의 일부 구간만 다른 컨텍스트로 실행합니다(`withContext`). 위 예제에서 `withContext` 블록이 끝나자 이름이 다시 "화면"으로 돌아왔습니다. 컨텍스트를 고친 것이 아니라 블록 동안만 다른 컨텍스트를 쓴 것이기 때문입니다. 코루틴은 가볍고 컨텍스트 합치기도 싸서, 매번 새로 만드는 방식이 부담이 되지 않습니다.

## ThreadLocal과의 차이 {#vs-thread-local}

컨텍스트는 `ThreadLocal`과 비교하면 이해하기 쉽습니다. `ThreadLocal`은 "스레드마다 따로 갖는 값"이고, 코루틴 컨텍스트는 "코루틴마다 따로 갖는 값"입니다. 그런데 코루틴은 일시 중단될 때마다 다른 스레드에서 재개될 수 있습니다. 값이 스레드에 붙어 있으면 코루틴이 스레드를 옮겨 다닐 때 값을 잃어버립니다.

```kotlin
// ThreadLocalVsContext.kt
import kotlinx.coroutines.*
import kotlin.coroutines.AbstractCoroutineContextElement
import kotlin.coroutines.CoroutineContext
import java.util.concurrent.Executors

// 스레드에 붙는 값
val requestIdLocal = ThreadLocal<String?>()

// 코루틴 컨텍스트에 붙는 값
class RequestId(val value: String) : AbstractCoroutineContextElement(RequestId) {
    companion object Key : CoroutineContext.Key<RequestId>
}

fun threadName(): String = Thread.currentThread().name

val otherThread = Executors.newSingleThreadExecutor { Thread(it, "other-thread") }.asCoroutineDispatcher()

fun main() = runBlocking<Unit> {
    // main 스레드의 ThreadLocal 에 값을 넣어 둡니다
    requestIdLocal.set("req-1")

    // 1. 다른 스레드에서 실행되는 코루틴은 그 값을 보지 못합니다
    launch(Dispatchers.Default) {
        println("1) ThreadLocal=${requestIdLocal.get()}, 스레드=${threadName()}")
    }.join()

    // 2. 컨텍스트 요소는 코루틴을 따라가므로 스레드가 바뀌어도 그대로입니다
    launch(Dispatchers.Default + RequestId("req-1")) {
        println("2) 컨텍스트=${currentCoroutineContext()[RequestId]?.value}, 스레드=${threadName()}")
        // 이름 붙인 스레드 하나짜리 디스패처로 옮겨 봅니다
        launch(otherThread) {
            println("3) 자식도 이어받음=${currentCoroutineContext()[RequestId]?.value}, 스레드=${threadName()}")
        }
    }.join()

    // 4. asContextElement 는 코루틴이 실행될 때마다 ThreadLocal 에 값을 넣어 줍니다
    launch(Dispatchers.Default + requestIdLocal.asContextElement("req-1")) {
        delay(10)
        println("4) ThreadLocal=${requestIdLocal.get()}, 스레드=${threadName()}")
    }.join()
    otherThread.close()
}
```

```text
1) ThreadLocal=null, 스레드=DefaultDispatcher-worker-1
2) 컨텍스트=req-1, 스레드=DefaultDispatcher-worker-1
3) 자식도 이어받음=req-1, 스레드=other-thread
4) ThreadLocal=req-1, 스레드=DefaultDispatcher-worker-1
```

1. `main` 스레드에 넣은 `ThreadLocal` 값은 `Dispatchers.Default`의 스레드에서 보이지 않습니다.
2. 같은 값을 컨텍스트 요소로 넣으면 어느 스레드에서 실행되든 보입니다.
3. 자식 코루틴은 부모 컨텍스트를 이어받으므로, 스레드가 `other-thread`로 바뀌어도 값이 그대로 있습니다.
4. 이미 `ThreadLocal`을 읽는 코드(로깅 라이브러리 등)가 있으면 `asContextElement`로 이어 줄 수 있습니다. 이 요소는 `ThreadContextElement`를 구현해서, 코루틴이 어떤 스레드에서 실행을 시작하거나 재개할 때 그 스레드의 `ThreadLocal`에 값을 넣고, 일시 중단될 때 원래 값으로 되돌려 놓습니다.

정리하면 둘의 차이는 둘입니다. 값이 붙는 대상이 스레드냐 코루틴이냐, 그리고 값을 고칠 수 있느냐입니다. `ThreadLocal`은 `set`으로 아무 때나 고치지만, 컨텍스트는 위에서 본 것처럼 고칠 수 없고 새로 만들어야 합니다.

## 직접 만드는 요소 {#custom-element}

`CoroutineName`과 같은 모양으로 요소를 직접 만들 수 있습니다. `AbstractCoroutineContextElement`를 상속하고 `companion object`를 키로 두면 됩니다. 요청 ID, 로그인 사용자, 추적(tracing) 정보처럼 "이 작업 전체에 따라다녀야 하는 값"을 넣는 데 씁니다. 함수마다 매개변수로 넘기지 않아도 되고, 위에서 본 것처럼 스레드가 바뀌어도 잃어버리지 않습니다.

```kotlin
// AuthUser.kt
import kotlinx.coroutines.*
import kotlin.coroutines.AbstractCoroutineContextElement
import kotlin.coroutines.CoroutineContext

// 로그인한 사용자를 담는 컨텍스트 요소
class AuthUser(val name: String) : AbstractCoroutineContextElement(AuthUser) {
    companion object Key : CoroutineContext.Key<AuthUser>
    override fun toString(): String = "AuthUser($name)"
}

suspend fun loadOrders() {
    val user = currentCoroutineContext()[AuthUser]
        ?: throw SecurityException("로그인하지 않았습니다")
    println("${user.name}의 주문을 불러옵니다")
}

fun main() = runBlocking<Unit> {
    // 1. 컨텍스트에 넣어 두면 그 아래 어디서든 꺼낼 수 있습니다
    launch(AuthUser("창국")) {
        loadOrders()
        // 2. 자식 코루틴도 이어받습니다
        launch { loadOrders() }
    }.join()

    // 3. 같은 키로 다시 넣으면 그 블록 안에서만 바뀝니다
    launch(AuthUser("창국")) {
        withContext(AuthUser("관리자")) { loadOrders() }
        loadOrders()
    }.join()

    // 4. 넣지 않았으면 null 이 나옵니다
    try {
        loadOrders()
    } catch (e: SecurityException) {
        println("실패: ${e.message}")
    }
}
```

```text
창국의 주문을 불러옵니다
창국의 주문을 불러옵니다
관리자의 주문을 불러옵니다
창국의 주문을 불러옵니다
실패: 로그인하지 않았습니다
```

`loadOrders`는 사용자를 매개변수로 받지 않는데도 지금 코루틴의 사용자를 알아냅니다. 다만 이 편리함은 의존 관계를 숨긴다는 뜻이기도 합니다. 함수 시그니처만 봐서는 이 함수가 `AuthUser`를 필요로 한다는 사실이 보이지 않고, 넣는 것을 잊으면 컴파일러가 아니라 실행 중 예외로 알게 됩니다. 비즈니스 로직에 꼭 필요한 값은 매개변수로 넘기고, 로그·추적처럼 곁다리로 따라다니는 정보에 컨텍스트 요소를 쓰는 것이 일반적입니다.

## 컨텍스트를 읽는 두 경로 {#reading-context}

`coroutineContext`라는 같은 이름으로 접근하는 것이 실제로는 두 가지입니다.

```kotlin
// CoroutineScope.kt (kotlinx-coroutines) — 스코프가 들고 있는 컨텍스트
public interface CoroutineScope {
    public val coroutineContext: CoroutineContext
}

// Continuation.kt (kotlin 표준 라이브러리) — 지금 실행 중인 코루틴의 컨텍스트
public suspend inline val coroutineContext: CoroutineContext
```

1. **`CoroutineScope.coroutineContext`** 는 스코프 객체의 프로퍼티입니다. `launch { }` 블록 안의 `this`가 스코프이므로 블록 안에서 그냥 `coroutineContext`라고 쓰면 이것이 읽힙니다.
2. **`kotlin.coroutines.coroutineContext`** 는 `suspend` 함수 안에서만 읽을 수 있는 최상위 프로퍼티입니다. 실제 구현은 없고, 컴파일러가 "지금 이 `suspend` 함수에 전달된 `Continuation`의 컨텍스트"를 읽는 코드로 바꿔 넣습니다. Q32에서 본 것처럼 모든 `suspend` 함수는 숨은 `Continuation` 매개변수를 받으므로 언제든 읽을 수 있습니다.

`launch` 블록 안에서는 둘이 같은 값입니다. 블록의 스코프가 곧 실행 중인 코루틴이기 때문입니다. 그런데 `CoroutineScope`를 수신 객체로 받는 `suspend` 함수에서는 둘이 갈립니다.

```kotlin
// NameClash.kt
import kotlinx.coroutines.*

// CoroutineScope 를 수신 객체로 받는 suspend 함수 (권장하지 않는 형태)
suspend fun CoroutineScope.printNames() {
    // 수신 객체(스코프)의 프로퍼티를 읽습니다
    println("1) coroutineContext: ${coroutineContext[CoroutineName]?.name}")
    // 지금 이 함수를 실행 중인 코루틴의 컨텍스트를 읽습니다
    println("2) currentCoroutineContext(): ${currentCoroutineContext()[CoroutineName]?.name}")
}

fun main() = runBlocking<Unit> {
    val otherScope = CoroutineScope(CoroutineName("다른 스코프"))
    withContext(CoroutineName("호출한 코루틴")) {
        otherScope.printNames()
    }
}
```

```text
1) coroutineContext: 다른 스코프
2) currentCoroutineContext(): 호출한 코루틴
```

함수 안에서 `coroutineContext`라고 쓰면 코틀린은 수신 객체의 프로퍼티를 먼저 고릅니다. 그래서 1)은 함수를 실행 중인 코루틴이 아니라 수신 객체로 넘어온 `otherScope`의 이름을 읽었습니다. 같은 이름이 서로 다른 것을 가리키는 함정입니다.

`currentCoroutineContext()`는 이 혼동을 피하려고 kotlinx-coroutines가 만든 함수입니다. 2번 경로(`kotlin.coroutines.coroutineContext`)를 그대로 돌려주지만 이름이 달라서 가려지지 않습니다. 라이브러리 문서는 충돌이 없는 곳에서도 `suspend` 함수 안에서는 이 함수를 쓰라고 권합니다. 이 토픽의 예제도 블록 안에서 `currentCoroutineContext()`를 썼습니다.

## 요약 {#summary}

코루틴 컨텍스트는 코루틴의 실행 설정을 담은 인덱싱된 집합입니다. 요소마다 `companion object`로 만든 키가 있고, 같은 키의 요소는 하나만 들어갑니다. 요소 하나도 그 자체로 컨텍스트라서 `+`로 바로 합칠 수 있습니다. 디스패처는 모두 `ContinuationInterceptor`라는 같은 키를 씁니다.

대표 요소는 넷입니다. `Job`은 코루틴마다 새로 만들어지고 물려받은 `Job`은 부모로 연결됩니다. 디스패처는 시작과 재개 때마다 실행할 스레드를 고릅니다. `CoroutineName`은 디버그 모드에서 스레드 이름에 붙어 보입니다. `CoroutineExceptionHandler`는 맨 위 코루틴의 것만 쓰입니다.

컨텍스트는 불변이라 여러 코루틴과 스레드가 잠금 없이 공유합니다. 바꾸려면 새 코루틴을 시작하거나 `withContext`로 구간만 다른 컨텍스트로 실행합니다. 스레드에 붙는 `ThreadLocal`과 달리 코루틴을 따라다니므로 스레드가 바뀌어도 값이 유지되고, 요소를 직접 만들어 요청 ID 같은 값을 실어 보낼 수 있습니다. `suspend` 함수 안에서 컨텍스트를 읽을 때는 `currentCoroutineContext()`를 씁니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) context[CoroutineName] 에서 대괄호 안의 CoroutineName 은 무엇인가요?">

클래스가 아니라 `CoroutineName` 클래스의 `companion object Key`입니다. 코틀린에서 클래스 이름만 쓰면 그 클래스의 `companion object`를 가리킵니다.

이 `Key`는 `CoroutineContext.Key<CoroutineName>`을 구현하고 있어서, `get` 연산자의 결과 타입이 `CoroutineName?`으로 정해집니다. 요소 자신도 생성자에서 같은 `Key`를 자기 키로 등록하므로, 컨텍스트는 키가 같은지만 비교해서 요소를 찾습니다.

</def>
<def title="Q) Dispatchers.Main + Dispatchers.IO 를 하면 어떻게 되나요?">

`Dispatchers.IO` 하나만 남습니다. 디스패처는 모두 `ContinuationInterceptor`라는 같은 키를 쓰고, 컨텍스트에는 같은 키의 요소가 하나만 들어가며, `+`에서는 오른쪽이 이기기 때문입니다.

디스패처가 같은 키를 쓰는 이유는 디스패처가 `Continuation`의 재개를 가로채는 인터셉터의 한 종류이기 때문입니다. 한 코루틴의 재개를 두 인터셉터가 동시에 맡을 수는 없습니다.

</def>
<def title="Q) 코루틴 컨텍스트를 불변으로 만든 이유는 무엇인가요?">

컨텍스트가 여러 코루틴에 공유되기 때문입니다. 부모 컨텍스트는 여러 자식이 함께 참조하고, 자식들은 서로 다른 스레드에서 실행될 수 있습니다. 고칠 수 있다면 다른 코루틴의 설정까지 바뀌고 동시 접근도 막아야 합니다. 불변이면 잠금 없이 공유할 수 있습니다.

설정을 바꿀 때는 새 코루틴을 시작하거나 `withContext`로 블록 동안만 다른 컨텍스트로 실행합니다. 블록이 끝나면 원래 컨텍스트로 돌아갑니다.

</def>
<def title="Q) ThreadLocal 대신 코루틴 컨텍스트 요소를 써야 하는 이유는 무엇인가요?">

코루틴은 일시 중단 후 다른 스레드에서 재개될 수 있어서, 스레드에 붙은 `ThreadLocal` 값은 코루틴이 스레드를 옮기면 보이지 않습니다. 컨텍스트 요소는 코루틴에 붙어 있고 자식에게도 이어지므로 어느 스레드에서 실행되든 그대로 읽힙니다.

이미 `ThreadLocal`을 읽는 코드가 있으면 `threadLocal.asContextElement(값)`을 컨텍스트에 넣습니다. 코루틴이 실행을 시작하거나 재개할 때 그 스레드의 `ThreadLocal`에 값을 넣고, 일시 중단될 때 되돌려 놓습니다.

</def>
<def title="Q) suspend 함수 안에서 coroutineContext 대신 currentCoroutineContext() 를 권하는 이유는 무엇인가요?">

`coroutineContext`라는 이름이 두 가지를 가리키기 때문입니다. 하나는 `CoroutineScope`의 프로퍼티(스코프가 들고 있는 컨텍스트)이고, 하나는 `suspend` 함수에서만 읽을 수 있는 최상위 프로퍼티(지금 실행 중인 코루틴의 컨텍스트)입니다.

`CoroutineScope`를 수신 객체로 받는 `suspend` 함수에서는 수신 객체의 프로퍼티가 먼저 골라져서, 실행 중인 코루틴과 다른 스코프의 컨텍스트를 읽게 됩니다. `currentCoroutineContext()`는 항상 실행 중인 코루틴의 컨텍스트를 돌려주므로 이런 혼동이 없습니다.

</def>
</deflist>
