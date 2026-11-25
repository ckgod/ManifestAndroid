# Details: GlobalScope를 신중하게 써야 하는 이유

`GlobalScope.launch { }`는 스코프를 따로 만들 필요가 없어서 "시작해 두고 잊어버리는" 작업에 편해 보입니다. 하지만 kotlinx-coroutines는 이 객체에 `@DelicateCoroutinesApi`를 붙여, 쓰는 곳마다 컴파일러가 경고를 내게 해 두었습니다.

```text
warning: this is a delicate API and its use requires care. Make sure you fully read and
understand documentation of the declaration that is marked as a delicate API.
```

이 토픽에서는 그 이유를 구현에서부터 봅니다. 결론부터 말하면 문제는 하나입니다. **`GlobalScope`에서 시작한 코루틴에는 부모가 없습니다.** 누수, 낭비되는 작업, 테스트의 어려움은 모두 여기서 나옵니다.

예제는 Kotlin 2.4.21, kotlinx-coroutines 1.11.0(테스트는 kotlinx-coroutines-test 1.11.0), JDK 25에서 실행했습니다.

## 빈 컨텍스트 {#empty-context}

```kotlin
// CoroutineScope.kt (kotlinx-coroutines 1.11.0)
@DelicateCoroutinesApi
public object GlobalScope : CoroutineScope {
    override val coroutineContext: CoroutineContext
        get() = EmptyCoroutineContext
}
```

`GlobalScope.launch { }`를 부르면 빌더는 이 빈 컨텍스트를 부모 컨텍스트로 씁니다([컨텍스트 합치기](Q34-coroutine-builder.md#new-context)).

- **`Job`이 없습니다.** 새 코루틴이 등록될 부모가 없으므로 맨 위 코루틴이 됩니다. 이 코루틴을 기다려 주는 쪽도, 대신 취소해 주는 쪽도 없습니다. 끝나는 때는 스스로 완료하거나 실패할 때, 아니면 프로세스가 끝날 때뿐입니다.
- **디스패처가 없습니다.** 그래서 `launch`가 `Dispatchers.Default`를 붙이고, 코루틴은 공유 스레드 풀에서 실행됩니다.

구조화된 동시성(structured concurrency)은 "모든 코루틴은 부모 안에서 시작되고, 부모는 자식이 끝나야 끝난다"는 규칙입니다. `GlobalScope`는 이 규칙 바깥에서 코루틴을 시작하는 통로입니다.

## 기다려 주지 않음 {#no-waiting}

`runBlocking` 안에서 시작해도 `GlobalScope` 코루틴은 `runBlocking`의 자식이 아닙니다.

```kotlin
// GlobalNoParent.kt
import kotlinx.coroutines.*

@OptIn(DelicateCoroutinesApi::class)
fun main() {
    runBlocking {
        // 1. runBlocking 의 자식: runBlocking 이 끝날 때까지 기다려 줍니다
        launch {
            delay(100)
            println("1) 자식 끝")
        }
        // 2. GlobalScope 에서 시작: runBlocking 과 아무 관계가 없습니다
        GlobalScope.launch {
            delay(300)
            println("2) GlobalScope 코루틴 끝")
        }
    }
    println("runBlocking 반환")
    Thread.sleep(500)   // 프로세스가 바로 끝나지 않게 잠시 붙잡아 둡니다
    println("main 끝")
}
```

```text
1) 자식 끝
runBlocking 반환
2) GlobalScope 코루틴 끝
main 끝
```

`runBlocking`은 자식 1)이 끝나자마자 돌아왔고, 2)는 그 뒤에 혼자 끝났습니다. 마지막의 `Thread.sleep(500)`을 지우면 2)는 아예 찍히지 않습니다. `Dispatchers.Default`의 스레드는 데몬 스레드(daemon thread, 프로그램 종료를 막지 않는 스레드)라서 `main`이 끝나면 작업이 중간에 사라집니다.

취소도 마찬가지로 닿지 않습니다.

```kotlin
// GlobalCancel.kt
import kotlinx.coroutines.*

@OptIn(DelicateCoroutinesApi::class)
fun main() = runBlocking<Unit> {
    val screen = launch {
        // 화면에 속한 작업
        launch {
            delay(500)
            println("1) 화면 작업 끝")
        }
        // 화면에서 시작했지만 GlobalScope 에 맡긴 작업
        GlobalScope.launch {
            delay(500)
            println("2) GlobalScope 작업 끝")
        }
    }
    delay(100)
    screen.cancel()   // 화면이 닫혔습니다
    println("화면 취소")
    delay(1000)
}
```

```text
화면 취소
2) GlobalScope 작업 끝
```

`screen`을 취소하자 1)은 함께 취소됐지만, 2)는 `screen` 안에서 시작했는데도 끝까지 실행됐습니다. 코드에서 어디에 적혔는지가 아니라 **어느 스코프에서 시작했는지**가 부모를 정하기 때문입니다.

## 메모리 누수 {#memory-leak}

부모가 없는 코루틴이 수명이 짧은 객체를 참조하면, 그 객체가 쓰임을 다한 뒤에도 메모리에서 해제되지 않습니다.

```kotlin
// GlobalScopeLeak.kt (안드로이드 예시, 실행하지 않음)
class MyActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        @OptIn(DelicateCoroutinesApi::class)
        GlobalScope.launch {
            delay(10_000)   // 오래 걸리는 작업 흉내
            updateUi()      // this@MyActivity 를 참조합니다
        }
    }

    private fun updateUi() { /* ... */ }
}
```

블록 안에서 `updateUi()`를 부르므로, 컴파일러가 만든 코루틴 객체는 `MyActivity` 인스턴스를 필드로 들고 있습니다. 사용자가 화면을 회전하거나 뒤로 가면 `Activity`는 파괴되지만, 아직 `delay` 중인 코루틴이 그 인스턴스를 붙잡고 있어서 가비지 컬렉터가 회수하지 못합니다. 10초 뒤에는 이미 파괴된 화면을 갱신하려 들고, 화면을 여러 번 열고 닫으면 붙잡힌 `Activity`가 그만큼 쌓입니다.

`lifecycleScope.launch { }`로 바꾸면 `Activity`가 DESTROYED가 될 때 코루틴이 취소되고, 코루틴 객체가 사라지면서 참조도 풀립니다.

서버처럼 프로세스가 오래 사는 환경에서는 더 심각합니다. 끝나는 조건이 없는 `GlobalScope` 코루틴은 프로세스가 살아 있는 내내 남아 있고, 요청마다 하나씩 시작하면 메모리와 스레드 사용량이 계속 늘어납니다.

## 쓸모없어진 작업 {#wasted-work}

메모리를 붙잡지 않더라도, 결과를 받을 쪽이 사라진 작업이 계속 돕니다.

```kotlin
// WastedWork.kt (안드로이드 예시, 실행하지 않음)
@OptIn(DelicateCoroutinesApi::class)
fun loadDataForScreen() {
    GlobalScope.launch {
        val data = networkApi.fetchData()   // 5초 걸립니다
        // 이때 사용자는 이미 화면을 떠났을 수 있습니다
        updateScreenWith(data)
    }
}
```

사용자가 화면을 떠나면 이 데이터는 필요 없습니다. 그래도 코루틴은 네트워크 요청을 끝까지 보내고 결과를 처리하면서 CPU, 배터리, 데이터를 씁니다. `viewModelScope`에서 시작했다면 `ViewModel`이 정리될 때 요청이 취소됐을 것입니다.

## 예외가 가는 곳 {#exception}

부모가 없으므로 실패도 받아 줄 곳이 없습니다. `GlobalScope.launch`에서 잡히지 않은 예외는 시작한 쪽의 `try-catch`로 오지 않고, 스레드의 기본 예외 처리기로 갑니다.

```kotlin
// GlobalCrash.kt
import kotlinx.coroutines.*

@OptIn(DelicateCoroutinesApi::class)
fun main() = runBlocking<Unit> {
    // try-catch 로 감싸도 잡히지 않습니다
    try {
        GlobalScope.launch {
            throw IllegalStateException("동기화 실패")
        }.join()
    } catch (e: IllegalStateException) {
        println("잡음: ${e.message}")
    }
    println("runBlocking 은 계속 실행")
}
```

```text
Exception in thread "DefaultDispatcher-worker-1" java.lang.IllegalStateException: 동기화 실패
	...
runBlocking 은 계속 실행
```

`join()`은 실패한 코루틴이 끝나기를 기다릴 뿐 예외를 다시 던지지 않습니다. JVM 콘솔 프로그램에서는 스택 트레이스만 찍히고 지나가지만, 안드로이드의 기본 처리기는 앱을 종료시킵니다. 컨텍스트에 `CoroutineExceptionHandler`를 넣지 않는 한 이 예외를 처리할 곳이 없습니다.

## 테스트하기 어려움 {#testing}

코루틴 테스트는 `runTest`를 씁니다. `runTest`의 스코프에서 시작한 코루틴은 테스트 스케줄러 위에서 돌아서, `delay`가 실제로 기다리지 않고 가상 시간으로 건너뜁니다. `GlobalScope` 코루틴은 이 스코프의 컨텍스트를 이어받지 않으므로 테스트 스케줄러 밖에서 실제 시간으로 돕니다.

```kotlin
// GlobalTest.kt
import kotlinx.coroutines.*
import kotlinx.coroutines.test.*

class Syncer(private val scope: CoroutineScope) {
    var synced = false

    // 바깥에서 받은 스코프에서 시작합니다
    fun syncWithScope() {
        scope.launch {
            delay(10_000)   // 10초 걸리는 동기화 흉내
            synced = true
        }
    }

    // GlobalScope 에서 시작합니다
    @OptIn(DelicateCoroutinesApi::class)
    fun syncWithGlobal() {
        GlobalScope.launch {
            delay(10_000)
            synced = true
        }
    }
}

fun main() {
    // 1. 테스트 스코프를 넘기면 delay 가 가상 시간으로 처리됩니다
    runTest {
        val syncer = Syncer(this)
        syncer.syncWithScope()
        delay(10_001)   // 가상 시간이라 실제로는 기다리지 않습니다
        println("1) synced=${syncer.synced}")
    }

    // 2. GlobalScope 코루틴은 테스트 스케줄러 밖에서 실제 시간으로 기다립니다
    runTest {
        val syncer = Syncer(this)
        syncer.syncWithGlobal()
        delay(10_001)
        println("2) synced=${syncer.synced}")
    }
}
```

```text
1) synced=true
2) synced=false
```

두 테스트 모두 실제로 10초를 기다리지 않고 바로 끝났습니다. 1)은 테스트가 가상 시간 10초를 건너뛰어 동기화가 끝난 상태를 확인했습니다. 2)는 동기화가 실제 시간으로 10초를 기다리는 중이라 테스트가 끝날 때까지 `synced`가 바뀌지 않았습니다. 이 코드를 테스트하려면 실제로 10초를 재우거나 결과를 반복해서 확인하는 우회 코드가 필요하고, 그런 테스트는 느리고 가끔씩 실패합니다.

`Syncer`가 스코프를 생성자로 받도록 만든 것이 1)을 가능하게 한 부분입니다. 스코프를 바깥에서 받으면 실제 앱에서는 앱 스코프를, 테스트에서는 테스트 스코프를 넣을 수 있습니다.

## 대안 {#alternatives}

코루틴을 시작하는 쪽의 생명주기에 맞는 스코프를 씁니다.

| 시작하는 곳 | 쓸 스코프 |
|---|---|
| `ViewModel` | `viewModelScope` |
| `Activity`, `Fragment` | `lifecycleScope` |
| 직접 만든 클래스 | 프로퍼티로 만든 `CoroutineScope(...)`, 클래스가 끝날 때 `cancel()` |
| `suspend` 함수 안에서 여러 작업을 동시에 | `coroutineScope { }` |

앱이 살아 있는 동안 계속 돌아야 하는 작업(주기적인 통계 전송, 화면과 무관한 동기화)은 `GlobalScope`를 쓸 만한 드문 경우입니다. 이때도 앱 전용 스코프를 하나 만들어 주입하는 편이 낫습니다.

```kotlin
// ApplicationScope.kt (예시, 실행하지 않음)
class MyApplication : Application() {
    // 앱 전체에서 쓰는 스코프. 작업 하나의 실패가 다른 작업을 멈추지 않게 SupervisorJob 을 씁니다
    val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
}

class AnalyticsUploader(private val scope: CoroutineScope) {
    fun start() {
        scope.launch { /* 주기적으로 전송 */ }
    }
}
```

`GlobalScope`와 하는 일은 같지만 세 가지가 다릅니다.

1. 스코프가 이름을 가진 값이라 어디서 쓰는지 찾을 수 있고, 테스트에서는 테스트 스코프로 바꿔 넣을 수 있습니다.
2. 컨텍스트에 `CoroutineExceptionHandler`를 넣어 실패를 한곳에서 기록할 수 있습니다.
3. `Job`이 있으므로 필요하면 한꺼번에 취소할 수 있습니다.

## 요약 {#summary}

`GlobalScope`의 컨텍스트는 `EmptyCoroutineContext`라서 `Job`도 디스패처도 없습니다. 여기서 시작한 코루틴은 부모가 없는 맨 위 코루틴이 되어, 시작한 곳이 끝나도 기다려 주지 않고 취소되어도 함께 취소되지 않습니다.

그 결과 짧게 사는 객체를 붙잡아 메모리 누수를 만들고, 결과를 받을 쪽이 사라진 작업을 계속 돌리고, 잡히지 않은 예외를 스레드 기본 처리기로 보내고, 테스트 스케줄러의 제어를 벗어납니다. 대신 시작하는 곳의 생명주기에 맞는 스코프를 쓰고, 앱 전체 수명의 작업도 앱 전용 스코프를 만들어 주입합니다.
