# Q37) 코루틴 스코프

코루틴 스코프(`CoroutineScope`)는 코루틴을 시작하는 자리입니다. 어떤 스코프에서 `launch`나 `async`를 부르느냐에 따라 새 코루틴이 어느 스레드에서 실행되는지, 누구의 자식이 되는지, 언제 함께 취소되는지가 정해집니다. 그래서 스코프를 고르는 것은 "이 작업을 무엇의 생명주기에 묶을 것인가"를 고르는 일입니다.

Q34에서 빌더가 스코프의 컨텍스트를 이어받는 과정을, Q35에서 컨텍스트에 든 요소를, Q36에서 `Job`의 부모·자식 관계를 봤습니다. 이 토픽에서는 그 셋을 하나로 묶는 스코프 쪽에서 봅니다. 인터페이스가 얼마나 작은지, `CoroutineScope()` 함수가 무엇을 덧붙이는지, 스코프를 객체의 생명주기에 묶는 법, 미리 만들어진 스코프들의 구성, 그리고 스코프 인스턴스와 `coroutineScope { }` 함수의 차이입니다.

심화 주제는 따로 나눴습니다.

- [GlobalScope를 신중하게 써야 하는 이유](Details-GlobalScope를-신중하게-써야-하는-이유.md)
- [coroutineScope 함수](Details-coroutineScope-함수.md)
- [supervisorScope 함수](Details-supervisorScope-함수.md)

예제는 Kotlin 2.4.21, kotlinx-coroutines 1.11.0, JDK 25에서 실행했습니다. 라이브러리 내부 코드도 같은 버전의 소스에서 옮겼습니다.

## 프로퍼티 하나짜리 인터페이스 {#interface}

`CoroutineScope` 인터페이스에는 프로퍼티가 하나뿐입니다.

```kotlin
// CoroutineScope.kt (kotlinx-coroutines 1.11.0)
public interface CoroutineScope {
    public val coroutineContext: CoroutineContext
}
```

코루틴을 시작하거나 취소하는 코드는 인터페이스 안에 없습니다. 그런 기능은 모두 `CoroutineScope`의 **확장 함수**로 바깥에 있습니다.

```kotlin
// 확장 함수들의 선언부만 모았습니다 (kotlinx-coroutines 1.11.0)
public fun CoroutineScope.launch(...): Job
public fun <T> CoroutineScope.async(...): Deferred<T>
public fun CoroutineScope.cancel(cause: CancellationException? = null)
public val CoroutineScope.isActive: Boolean
public operator fun CoroutineScope.plus(context: CoroutineContext): CoroutineScope
```

확장 함수들은 모두 스코프의 `coroutineContext`만 읽어서 일합니다.

- `launch`, `async`는 이 컨텍스트를 새 코루틴의 부모 컨텍스트로 씁니다([컨텍스트 합치기](Q34-coroutine-builder.md#new-context)). 컨텍스트 안의 `Job`이 새 코루틴의 부모가 됩니다.
- `cancel()`은 컨텍스트에서 `Job`을 꺼내 취소합니다.
- `isActive`는 컨텍스트의 `Job`이 활성인지 봅니다. `Job`이 없으면 `true`입니다.
- `scope + Dispatchers.IO`는 컨텍스트를 합친 새 스코프를 만듭니다.

즉 스코프는 **코루틴 컨텍스트를 들고 있는 상자**이고, 그 컨텍스트 안의 `Job`이 이 스코프에서 시작한 모든 코루틴의 부모 역할을 합니다. 스코프를 취소한다는 말은 이 부모 `Job`을 취소한다는 뜻이고, Q36에서 본 것처럼 부모가 취소되면 자식은 모두 취소됩니다.

`launch { }` 블록 안의 `this`도 `CoroutineScope`입니다. 새로 만들어진 코루틴 객체가 스코프 인터페이스를 함께 구현하기 때문입니다([AbstractCoroutine의 내부 구조](Details-AbstractCoroutine의-내부-구조.md#three-roles)). 그래서 블록 안에서 다시 `launch`를 부르면 지금 코루틴이 부모가 됩니다.

## 스코프와 컨텍스트의 구분 {#scope-vs-context}

스코프는 컨텍스트 하나를 감싼 것뿐이라서, 둘이 왜 따로 있는지 의문이 들 수 있습니다. 차이는 쓰임새입니다.

| | `CoroutineScope` | `CoroutineContext` |
|---|---|---|
| 무엇인가 | 코루틴을 **시작하는 곳** | 코루틴의 **설정 묶음** |
| 주로 하는 일 | `launch`, `async`의 수신 객체, `cancel()`의 대상 | 빌더 인자, `withContext` 인자, 자식에게 물려줄 값 |
| 어디에 두나 | 클래스 프로퍼티처럼 생명주기를 가진 곳 | 요소끼리 `+`로 합쳐 넘기는 값 |

`CoroutineScope`라는 타입이 따로 있기 때문에 "이 함수는 코루틴을 시작한다"는 사실이 함수 선언에 드러납니다. 아래 [스코프 인스턴스와 coroutineScope 함수](#scope-object-vs-function)에서 이 약속을 다시 봅니다.

## CoroutineScope() 함수 {#factory}

스코프를 직접 만들 때는 `CoroutineScope(context)` 함수를 씁니다. 이름이 대문자로 시작하지만 생성자가 아니라 함수입니다. 인터페이스는 생성자를 가질 수 없으므로, 인터페이스와 같은 이름의 함수를 만들어 생성자처럼 보이게 한 것입니다. `Job()`, `SupervisorJob()`도 같은 방식의 함수입니다.

그래서 `CoroutineScope`라는 이름은 문맥에 따라 세 가지를 가리킵니다.

| 쓰인 모양 | 가리키는 것 | 예 |
|---|---|---|
| 타입 자리 | 인터페이스 | `private val scope: CoroutineScope`, `fun CoroutineScope.startUpload()` |
| 괄호를 붙여 호출 | 스코프를 만드는 함수 | `CoroutineScope(Dispatchers.IO)` |
| 실제로 만들어진 값 | 인터페이스를 구현한 인스턴스 | 함수가 돌려준 `ContextScope`, `GlobalScope`, `launch` 블록의 `this` |

이 토픽에서 "스코프"라고만 쓰면 셋째, 즉 인터페이스를 구현해서 실제로 만들어진 인스턴스를 말합니다. `launch`를 부르고 `cancel()`하는 대상은 언제나 이 인스턴스입니다.

```kotlin
// CoroutineScope.kt (kotlinx-coroutines 1.11.0)
public fun CoroutineScope(context: CoroutineContext): CoroutineScope =
    ContextScope(if (context[Job] != null) context else context + Job())

// Scopes.kt — 받은 컨텍스트를 그대로 들고만 있는 구현체입니다
internal class ContextScope(context: CoroutineContext) : CoroutineScope {
    override val coroutineContext: CoroutineContext = context
}
```

넘긴 컨텍스트에 `Job`이 없으면 **`Job()`을 하나 붙여 줍니다.** 스코프에 `Job`이 있어야 이 스코프에서 시작한 코루틴들이 한 부모 아래로 모이고, 그 부모를 취소해서 한꺼번에 정리할 수 있기 때문입니다.

```kotlin
// ScopeCancel.kt
import kotlinx.coroutines.*

fun main() {
    // 1. Job 을 넣지 않고 만든 스코프에도 Job 이 들어 있습니다
    val scope = CoroutineScope(Dispatchers.Default)
    println("1) Job 있음? ${scope.coroutineContext[Job] != null}")

    // 2. 스코프를 취소하면 그 안에서 시작한 코루틴이 모두 취소됩니다
    val first = scope.launch { delay(1000) }
    val second = scope.launch { delay(1000) }
    scope.cancel()
    runBlocking {
        first.join()
        second.join()
    }
    println("2) 취소됨? ${first.isCancelled}, ${second.isCancelled}")

    // 3. 취소된 스코프에서 새로 시작한 코루틴은 바로 취소됩니다
    val late = scope.launch { println("실행되지 않습니다") }
    runBlocking { late.join() }
    println("3) 늦게 시작한 코루틴 취소됨? ${late.isCancelled}")

    // 4. Job 이 없는 스코프는 취소할 수 없습니다
    @OptIn(DelicateCoroutinesApi::class)
    val noJobScope = GlobalScope + Dispatchers.Default
    try {
        noJobScope.cancel()
    } catch (e: IllegalStateException) {
        println("4) ${e.message}")
    }
}
```

```text
1) Job 있음? true
2) 취소됨? true, true
3) 늦게 시작한 코루틴 취소됨? true
4) Scope cannot be cancelled because it does not have a job: CoroutineScope(coroutineContext=Dispatchers.Default)
```

- 2)는 스코프 하나를 취소해서 그 안의 코루틴 둘을 정리했습니다. 스코프를 쓰는 가장 큰 이유입니다.
- 3)처럼 한 번 취소한 스코프는 다시 쓸 수 없습니다. 부모 `Job`이 이미 취소 상태라서 새 자식은 시작하자마자 취소됩니다. 정리 후에도 계속 써야 하는 스코프라면 스코프 대신 `scope.coroutineContext.cancelChildren()`으로 자식만 취소합니다.
- 4)는 `Job`이 없는 스코프입니다. `+`는 `CoroutineScope()` 함수를 거치지 않으므로 `Job`이 붙지 않았고, 취소할 대상이 없어 예외가 났습니다.

## 객체의 생명주기에 묶기 {#binding-lifecycle}

스코프를 클래스의 프로퍼티로 두고, 그 객체를 더 쓰지 않을 때 취소하면 코루틴의 수명이 객체의 수명과 같아집니다.

```kotlin
// OwnedScope.kt
import kotlinx.coroutines.*

class ImageLoader {
    // 이 객체가 사는 동안만 쓰는 스코프입니다
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    fun load(name: String) {
        scope.launch {
            try {
                delay(500)   // 내려받는 시간 흉내
                println("$name 완료")
            } catch (e: CancellationException) {
                println("$name 취소됨")
                throw e
            }
        }
    }

    // 객체를 더 쓰지 않을 때 부릅니다
    fun close() {
        scope.cancel()
    }
}

fun main() = runBlocking<Unit> {
    val loader = ImageLoader()
    loader.load("a.png")
    loader.load("b.png")

    delay(100)
    loader.close()   // 둘 다 아직 내려받는 중입니다
    delay(1000)
    println("끝")
}
```

```text
b.png 취소됨
a.png 취소됨
끝
```

두 작업이 `Dispatchers.Default`의 서로 다른 스레드에서 실행되므로 앞 두 줄의 순서는 실행마다 바뀔 수 있습니다.

이 구성에서 정할 것은 두 가지입니다.

1. **`Job`과 `SupervisorJob` 중 무엇을 넣을까.** `load` 하나가 실패했을 때 다른 `load`까지 멈추면 안 되므로 `SupervisorJob`을 넣었습니다. `Job()`을 넣으면 한 번의 실패로 스코프 전체가 취소되어 그 뒤의 `load`가 모두 바로 취소됩니다([SupervisorJob](Details-SupervisorJob.md#vs-job)).
2. **누가 언제 `close()`를 부를까.** 스코프는 스스로 끝나지 않습니다. `close()`를 부르지 않으면 객체를 버린 뒤에도 코루틴이 계속 돌고, 그 코루틴이 객체를 붙잡고 있어서 메모리에서 해제되지도 않습니다.

책의 `MyRepository` 예제는 `Job`을 따로 변수에 담아 `job.cancel()`을 불렀습니다. 스코프에 `cancel()` 확장 함수가 있으므로 `Job`을 따로 들고 있을 필요는 없습니다.

## 미리 만들어진 스코프 {#built-in-scopes}

직접 만들지 않아도 쓸 수 있는 스코프들이 있습니다. 컨텍스트 구성과 누가 취소하는지만 보면 차이가 정리됩니다.

| 스코프 | 컨텍스트 | 취소하는 쪽 | 제공하는 곳 |
|---|---|---|---|
| `GlobalScope` | 비어 있음 (`EmptyCoroutineContext`) | 없음 | kotlinx-coroutines |
| `MainScope()` | `SupervisorJob() + Dispatchers.Main` | 직접 `cancel()` | kotlinx-coroutines |
| `viewModelScope` | `Dispatchers.Main.immediate + SupervisorJob()` | `ViewModel`이 정리될 때 자동 | AndroidX Lifecycle |
| `lifecycleScope` | `SupervisorJob() + Dispatchers.Main.immediate` | `Lifecycle`이 DESTROYED가 될 때 자동 | AndroidX Lifecycle |

### GlobalScope {#global-scope}

```kotlin
// CoroutineScope.kt (kotlinx-coroutines 1.11.0)
@DelicateCoroutinesApi
public object GlobalScope : CoroutineScope {
    override val coroutineContext: CoroutineContext
        get() = EmptyCoroutineContext
}
```

앱 전체에 하나뿐인 `object`이고 컨텍스트가 비어 있습니다. 컨텍스트에 `Job`이 없으므로 여기서 시작한 코루틴은 **부모가 없는 맨 위 코루틴**이 됩니다. 누구도 이 코루틴을 기다리거나 대신 취소해 주지 않습니다. 디스패처도 없으므로 `launch`가 `Dispatchers.Default`를 붙여서 실행합니다.

`@DelicateCoroutinesApi`가 붙어 있어서 그냥 쓰면 컴파일러가 "주의해서 써야 하는 API"라는 경고를 냅니다. 왜 조심해야 하는지는 [GlobalScope를 신중하게 써야 하는 이유](Details-GlobalScope를-신중하게-써야-하는-이유.md)에서 다룹니다.

### MainScope() {#main-scope}

```kotlin
// CoroutineScope.kt (kotlinx-coroutines 1.11.0)
public fun MainScope(): CoroutineScope = ContextScope(SupervisorJob() + Dispatchers.Main)
```

부를 때마다 새 스코프를 만드는 함수입니다. 메인(UI) 스레드에서 실행하고, `SupervisorJob`이라 작업 하나가 실패해도 다른 작업은 계속됩니다. 자동으로 취소되지 않으므로 앞의 `ImageLoader`처럼 주인 객체가 끝날 때 `cancel()`을 직접 불러야 합니다.

```kotlin
// MainScopeUsage.kt (안드로이드 예시, 실행하지 않음)
class PlayerController {
    private val scope = MainScope()

    fun play() {
        scope.launch { /* 메인 스레드에서 UI 갱신 */ }
    }

    fun release() {
        scope.cancel()
    }
}
```

`Dispatchers.Main`은 플랫폼이 제공해야 하는 디스패처입니다. 안드로이드는 `kotlinx-coroutines-android`, 데스크톱은 `kotlinx-coroutines-swing`·`-javafx`가 제공합니다. 순수 JVM 프로그램에서 쓰면 "Main 디스패처가 없다"는 예외가 납니다.

### viewModelScope {#view-model-scope}

`ViewModel`마다 하나씩 생기고, `ViewModel`이 정리될 때 자동으로 취소됩니다. 화면 회전처럼 구성이 바뀌어도 `ViewModel`은 살아 있으므로 그 동안에는 작업도 이어집니다. 내부 구현은 [SupervisorJob의 viewModelScope](Details-SupervisorJob.md#view-model-scope)에서 봤습니다.

### lifecycleScope {#lifecycle-scope}

`Activity`, `Fragment`처럼 `Lifecycle`을 가진 객체(`LifecycleOwner`)에 붙는 스코프입니다. AndroidX Lifecycle 2.11.0 소스입니다.

```kotlin
// LifecycleOwner.kt, Lifecycle.kt (androidx.lifecycle 2.11.0, 주석 줄임)
public val LifecycleOwner.lifecycleScope: LifecycleCoroutineScope
    get() = lifecycle.coroutineScope

public val Lifecycle.coroutineScope: LifecycleCoroutineScope
    get() {
        while (true) {
            // 1. 이미 만든 스코프가 있으면 그것을 돌려줍니다
            val existing = internalScopeRef.get() as LifecycleCoroutineScopeImpl?
            if (existing != null) {
                return existing
            }
            // 2. 없으면 새로 만들고, 다른 스레드보다 먼저 저장한 경우에만 등록합니다
            val newScope =
                LifecycleCoroutineScopeImpl(this, SupervisorJob() + Dispatchers.Main.immediate)
            if (internalScopeRef.compareAndSet(null, newScope)) {
                newScope.register()
                return newScope
            }
        }
    }
```

처음 읽을 때 한 번만 만들고 `Lifecycle` 안에 저장해 둡니다. `compareAndSet`은 "아직 `null`일 때만 저장"하는 원자적 연산이라서, 두 스레드가 동시에 처음 읽어도 스코프는 하나만 등록됩니다. 저장에 진 쪽은 반복문을 한 번 더 돌아 이긴 쪽의 스코프를 돌려받습니다.

취소는 생명주기 관찰자가 맡습니다.

```kotlin
// Lifecycle.kt (androidx.lifecycle 2.11.0, 주석 줄임)
internal class LifecycleCoroutineScopeImpl(
    override val lifecycle: Lifecycle,
    override val coroutineContext: CoroutineContext,
) : LifecycleCoroutineScope(), LifecycleEventObserver {
    init {
        // 이미 DESTROYED 인 Lifecycle 이면 만들자마자 취소합니다
        if (lifecycle.currentState == Lifecycle.State.DESTROYED) {
            coroutineContext.cancel()
        }
    }

    fun register() {
        // 관찰자 등록은 메인 스레드에서 해야 하므로 코루틴으로 넘깁니다
        launch(Dispatchers.Main.immediate) {
            if (lifecycle.currentState >= Lifecycle.State.INITIALIZED) {
                lifecycle.addObserver(this@LifecycleCoroutineScopeImpl)
            } else {
                coroutineContext.cancel()
            }
        }
    }

    override fun onStateChanged(source: LifecycleOwner, event: Lifecycle.Event) {
        // DESTROYED 가 되면 관찰을 멈추고 스코프를 취소합니다
        if (lifecycle.currentState <= Lifecycle.State.DESTROYED) {
            lifecycle.removeObserver(this)
            coroutineContext.cancel()
        }
    }
}
```

- 스코프 자신이 `LifecycleEventObserver`라서 생명주기 이벤트를 직접 받습니다. 상태가 DESTROYED가 되면 `coroutineContext.cancel()`로 `SupervisorJob`을 취소하고, 그 아래 코루틴이 모두 취소됩니다.
- 취소 시점이 **DESTROYED 하나뿐**이라는 점을 기억해 둡니다. 화면이 백그라운드로 가서 STOPPED가 되어도 `lifecycleScope`의 코루틴은 계속 실행됩니다. 화면이 보일 때만 데이터를 받고 싶다면 `repeatOnLifecycle(Lifecycle.State.STARTED) { }` 처럼 상태에 맞춰 블록을 시작하고 취소해 주는 함수를 함께 씁니다.
- `Dispatchers.Main.immediate`는 이미 메인 스레드에서 호출됐다면 다음 차례로 미루지 않고 그 자리에서 바로 실행하는 메인 디스패처입니다. 디스패처 종류는 Q38에서 다룹니다.

## 스코프 인스턴스와 coroutineScope 함수 {#scope-object-vs-function}

이름이 거의 같은 두 가지를 구분해야 합니다.

- **`CoroutineScope`** (대문자): 지금까지 본, 인터페이스를 구현한 스코프 인스턴스입니다. 인스턴스에서 `launch`를 부르면 코루틴을 시작만 하고 **바로 돌아옵니다.** 코루틴은 스코프의 수명 동안 따로 실행됩니다.
- **`coroutineScope { }`** (소문자): `suspend` 함수입니다. 블록을 실행할 임시 스코프를 만들고, 그 안에서 시작한 코루틴이 **모두 끝날 때까지 기다렸다가** 돌아옵니다.

kotlinx-coroutines는 이 차이를 함수 모양으로 드러내자는 관례를 둡니다. 코루틴을 시작해 놓고 바로 돌아오는 함수는 `CoroutineScope`의 확장 함수로, 일을 다 끝내고 돌아오는 함수는 `suspend` 함수로 만듭니다.

```kotlin
// ScopeVsSuspend.kt
import kotlinx.coroutines.*

// 1. CoroutineScope 의 확장 함수: 코루틴을 시작만 하고 바로 돌아옵니다
fun CoroutineScope.startUpload(name: String) {
    launch {
        delay(500)
        println("$name 업로드 끝")
    }
}

// 2. suspend 함수: 안에서 시작한 일이 다 끝나야 돌아옵니다
suspend fun upload(name: String) = coroutineScope {
    launch {
        delay(500)
        println("$name 업로드 끝")
    }
}

fun main() = runBlocking<Unit> {
    startUpload("A")
    println("startUpload 반환")

    upload("B")
    println("upload 반환")
}
```

```text
startUpload 반환
A 업로드 끝
B 업로드 끝
upload 반환
```

`startUpload`는 업로드가 끝나기 전에 돌아왔고, `upload`는 업로드가 끝난 뒤에 돌아왔습니다. 함수 선언만 보고도 호출한 쪽이 "돌아온 뒤에 작업이 아직 돌고 있을 수 있다"는 것을 알 수 있습니다.

`coroutineScope { }`가 기다리고 실패를 처리하는 방식은 [coroutineScope 함수](Details-coroutineScope-함수.md)에서, 자식의 실패를 서로 격리하는 판인 `supervisorScope { }`는 [supervisorScope 함수](Details-supervisorScope-함수.md)에서 봅니다.

## 요약 {#summary}

`CoroutineScope`는 `coroutineContext` 하나만 가진 인터페이스이고, `launch`·`async`·`cancel()`은 모두 이 컨텍스트를 읽는 확장 함수입니다. 컨텍스트 안의 `Job`이 스코프에서 시작한 모든 코루틴의 부모가 되므로, 스코프를 취소하면 그 코루틴들이 한꺼번에 취소됩니다.

`CoroutineScope(context)` 함수는 컨텍스트에 `Job`이 없으면 `Job()`을 붙여 줍니다. 직접 만든 스코프는 주인 객체가 끝날 때 `cancel()`해야 하고, 한 번 취소한 스코프는 다시 쓸 수 없습니다. 작업끼리 실패를 격리하려면 `SupervisorJob`을 넣습니다.

미리 만들어진 스코프 가운데 `GlobalScope`는 `Job`이 없어 부모 없는 코루틴을 만들고, `MainScope()`는 직접 취소해야 하며, `viewModelScope`와 `lifecycleScope`는 `SupervisorJob`과 메인 디스패처로 만들어져 각각 `ViewModel` 정리와 DESTROYED 때 자동으로 취소됩니다.

코루틴을 시작만 하고 돌아오는 함수는 `CoroutineScope`의 확장 함수로, 일을 끝내고 돌아오는 함수는 `coroutineScope { }`를 쓴 `suspend` 함수로 만듭니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) CoroutineScope 인터페이스에는 launch 가 없는데 어떻게 scope.launch { } 를 부를 수 있나요?">

`launch`가 `CoroutineScope`의 확장 함수이기 때문입니다. 인터페이스에는 `coroutineContext` 프로퍼티 하나만 있고, `launch`·`async`·`cancel()`·`isActive`는 모두 바깥에 확장 함수로 정의되어 있습니다.

이 확장 함수들은 수신 객체의 `coroutineContext`만 읽습니다. `launch`는 그 컨텍스트를 새 코루틴의 부모 컨텍스트로 쓰고, `cancel()`은 그 안의 `Job`을 꺼내 취소합니다.

</def>
<def title="Q) CoroutineScope(Dispatchers.IO) 처럼 Job 없이 만든 스코프도 cancel() 할 수 있나요?">

할 수 있습니다. `CoroutineScope()` 함수는 넘긴 컨텍스트에 `Job`이 없으면 `Job()`을 붙여서 스코프를 만들기 때문입니다.

반면 `GlobalScope + Dispatchers.IO`처럼 `+`로 만든 스코프는 이 함수를 거치지 않아 `Job`이 없고, `cancel()`을 부르면 "Scope cannot be cancelled because it does not have a job" 예외가 납니다.

</def>
<def title="Q) 한 번 cancel() 한 스코프에서 다시 launch 하면 어떻게 되나요?">

새 코루틴이 시작하자마자 취소됩니다. 스코프의 부모 `Job`이 이미 취소 상태이고, 취소된 부모에 붙은 자식은 바로 취소되기 때문입니다. 예외가 나지 않고 조용히 실행되지 않으므로 알아차리기 어렵습니다.

정리한 뒤에도 같은 스코프를 계속 써야 한다면 스코프 자체를 취소하지 말고 `scope.coroutineContext.cancelChildren()`으로 자식만 취소합니다.

</def>
<def title="Q) viewModelScope 와 lifecycleScope 가 SupervisorJob 을 쓰는 이유는 무엇인가요?">

한 화면에서 시작한 여러 작업이 서로 독립적이기 때문입니다. 일반 `Job`이면 작업 하나가 실패할 때 스코프 전체가 취소되어 다른 작업도 멈추고, 그 뒤로 스코프를 다시 쓸 수도 없습니다. `SupervisorJob`은 자식의 실패가 부모로 올라가지 않으므로 다른 작업과 스코프가 그대로 유지됩니다.

다만 두 스코프 모두 `CoroutineExceptionHandler`가 없으므로, 잡히지 않은 예외는 앱을 종료시킵니다. 실패 격리는 예외를 대신 처리해 준다는 뜻이 아닙니다.

</def>
<def title="Q) lifecycleScope 에서 시작한 코루틴은 화면이 백그라운드로 가면 멈추나요?">

멈추지 않습니다. `lifecycleScope`는 `Lifecycle`이 DESTROYED가 될 때만 취소됩니다. 화면이 가려져 STOPPED가 되어도 코루틴은 계속 실행됩니다.

화면이 보이는 동안에만 일하게 하려면 `repeatOnLifecycle(Lifecycle.State.STARTED) { }` 안에서 작업을 시작합니다. 이 함수는 STARTED가 될 때 블록을 시작하고 STOPPED가 될 때 취소하기를 반복합니다.

</def>
<def title="Q) CoroutineScope 의 확장 함수와 coroutineScope 를 쓴 suspend 함수는 언제 각각 쓰나요?">

코루틴을 시작해 놓고 바로 돌아와야 하면 `CoroutineScope`의 확장 함수로 만듭니다. 호출한 쪽은 함수가 돌아온 뒤에도 작업이 계속 실행된다는 것을 선언만 보고 압니다.

작업을 모두 끝내고 결과를 돌려줘야 하면 `coroutineScope { }`를 쓴 `suspend` 함수로 만듭니다. 안에서 여러 코루틴을 동시에 시작해도, 함수는 그 코루틴들이 모두 끝난 뒤에 돌아옵니다.

</def>
</deflist>
