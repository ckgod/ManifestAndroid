# Details: runBlocking을 신중하게 써야 하는 이유

`runBlocking`은 일반 함수에서 `suspend` 함수를 부를 수 있게 이어 주는 코루틴 빌더입니다. 어디서나 부를 수 있고 결과를 바로 돌려줘서 편해 보이지만, 코루틴이 끝날 때까지 **자기를 부른 스레드를 막습니다.** 비동기로 바꿔 주는 도구가 아니라, 비동기 작업이 끝날 때까지 기다리게 만드는 도구입니다. 그래서 어느 스레드에서 부르는지에 따라 안전할 수도 있고 앱을 멈출 수도 있습니다.

예제는 Kotlin 2.4.21, kotlinx-coroutines 1.11.0, JDK 25에서 실행했습니다.

## 내부 구현 {#implementation}

실제 소스는 공통 부분과 JVM 부분으로 나뉘어 있습니다. 흐름만 이름 붙인 의사 코드로 옮기면 이렇습니다.

```kotlin
// runBlocking (의사 코드, 실제 소스: kotlinx-coroutines 1.11.0 Builders.concurrent.kt, jvm/Builders.kt)
fun <T> runBlocking(context: CoroutineContext, block: suspend CoroutineScope.() -> T): T {
    // 1. 디스패처를 넘기지 않았으면, 지금 스레드 전용 이벤트 루프를 디스패처로 씁니다
    val eventLoop = currentThreadEventLoop()
    val newContext = GlobalScope.newCoroutineContext(context + eventLoop)   // 부모 Job 없음

    // 2. 막을 스레드로 "지금 스레드"를 기억해 둡니다
    val coroutine = BlockingCoroutine<T>(newContext, blockedThread = Thread.currentThread(), eventLoop)
    coroutine.start(CoroutineStart.DEFAULT, coroutine, block)

    // 3. 코루틴이 끝날 때까지 이 스레드에서 기다립니다
    return coroutine.joinBlocking()
}

// BlockingCoroutine 안
fun joinBlocking(): T {
    while (true) {
        // 이벤트 루프에 쌓인 할 일을 하나 실행하고, 다음 할 일까지 남은 시간을 받습니다
        val waitNanos = eventLoop.processNextEvent()
        if (isCompleted) break
        // 남은 시간만큼 스레드를 재웁니다. 코루틴이 끝나면 afterCompletion 이 깨웁니다
        parkNanos(waitNanos)
        if (Thread.interrupted()) cancelCoroutine(InterruptedException())
    }
    // 결과를 돌려주거나, 예외로 끝났으면 그 예외를 던집니다
    return resultOrThrow()
}
```

세 가지를 읽을 수 있습니다.

- **막는 스레드는 부른 스레드입니다.** `Thread.currentThread()`를 그대로 기억해 두었다가 그 스레드에서 `while (true)`를 돕니다. 메인 스레드에서 부르면 메인 스레드가 막힙니다.
- **안쪽 코루틴도 그 스레드에서 실행됩니다.** 디스패처를 넘기지 않으면 스레드 전용 이벤트 루프(할 일을 하나씩 꺼내 실행하는 반복문)가 디스패처가 되고, `processNextEvent()`가 그 할 일을 이 스레드에서 실행합니다. 할 일이 없으면 다음 할 일(예: `delay`가 끝나는 시각)까지 스레드를 재웁니다(`park`).
- **부모가 없는 최상위 코루틴입니다.** `GlobalScope.newCoroutineContext`로 만들기 때문에 부모 `Job`이 없습니다. 코루틴 안에서 `runBlocking`을 불러도 바깥 코루틴의 자식이 되지 않아서, 바깥 코루틴을 취소해도 안쪽 `runBlocking`은 취소되지 않습니다.

## 막힌 스레드 {#blocked-thread}

안드로이드 메인 스레드처럼 스레드 하나로 도는 디스패처를 만들고, 그 위에서 `runBlocking`을 불러 봤습니다.

```kotlin
// BlockingUiThread.kt
import kotlinx.coroutines.*
import java.util.concurrent.Executors

// 안드로이드 메인 스레드처럼 스레드 하나로 도는 디스패처를 흉내 냅니다
val ui = Executors.newSingleThreadExecutor { task -> Thread(task, "ui") }.asCoroutineDispatcher()

fun main() = runBlocking<Unit> {
    val start = System.currentTimeMillis()
    fun elapsed() = (System.currentTimeMillis() - start + 25) / 50 * 50   // 50ms 단위로 반올림

    // 100ms 마다 화면을 그린다고 치는 코루틴
    val frames = launch(ui) {
        repeat(6) {
            println("${elapsed()}ms 화면 갱신")
            delay(100)
        }
    }

    delay(150)
    launch(ui) {
        println("${elapsed()}ms 버튼 클릭: runBlocking 시작")
        runBlocking { delay(400) }   // ui 스레드를 400ms 동안 막습니다
        println("${elapsed()}ms runBlocking 끝")
    }

    frames.join()
    ui.close()
}
```

```text
0ms 화면 갱신
100ms 화면 갱신
150ms 버튼 클릭: runBlocking 시작
550ms runBlocking 끝
550ms 화면 갱신
650ms 화면 갱신
750ms 화면 갱신
850ms 화면 갱신
```

200ms, 300ms, 400ms, 500ms에 있어야 할 화면 갱신이 사라졌습니다. 안쪽은 `delay`로 기다렸지만, 그 `delay`를 감싼 `runBlocking`이 `ui` 스레드를 붙잡고 있어서 다른 코루틴이 그 스레드를 쓸 수 없었습니다. `runBlocking { delay(400) }` 대신 `delay(400)`이었다면 화면 갱신은 100ms 간격으로 계속되었을 것입니다. 실제 앱이라면 이 400ms 동안 화면이 멈추고, 메인 스레드가 5초 넘게 막히면 ANR(앱 응답 없음)이 납니다. 시간은 실행할 때마다 수십 ms씩 다를 수 있습니다.

## 교착 상태 {#deadlock}

막힌 스레드가 자기 자신을 기다리면 영원히 풀리지 않습니다.

```kotlin
// Deadlock.kt
import kotlinx.coroutines.*
import java.util.concurrent.Executors

val ui = Executors.newSingleThreadExecutor { task -> Thread(task, "ui") }.asCoroutineDispatcher()

fun main() = runBlocking<Unit> {
    val job = launch(ui) {
        println("ui 스레드에서 runBlocking 호출")
        runBlocking {
            // ui 스레드에서 실행해야 하는 작업. 그런데 ui 스레드는 바깥 runBlocking 이 막고 있습니다
            withContext(ui) {
                println("이 줄은 실행되지 않습니다")
            }
        }
    }

    val finished = withTimeoutOrNull(1000) { job.join() }
    println(if (finished == null) "1초가 지나도 끝나지 않음: 교착 상태" else "정상 종료")
    System.exit(0)   // 막힌 ui 스레드 때문에 프로그램이 끝나지 않으므로 강제로 끝냅니다
}
```

```text
ui 스레드에서 runBlocking 호출
1초가 지나도 끝나지 않음: 교착 상태
```

`withContext(ui)`는 `ui` 디스패처에 일을 맡기고 그 일이 끝나길 기다립니다. 그런데 `ui`의 유일한 스레드는 `runBlocking`이 막고 있어서 맡긴 일을 실행할 스레드가 없습니다. `runBlocking`은 안쪽이 끝나길, 안쪽은 스레드가 풀리길 서로 기다립니다. 안드로이드에서 메인 스레드에서 `runBlocking`을 부르고 그 안에서 `withContext(Dispatchers.Main)`나 메인 스레드로 돌아오는 API를 부르면 같은 일이 일어나 앱이 멈춘 채 풀리지 않습니다.

## 써도 되는 곳 {#when-to-use}

**`main` 함수와 테스트.** 일반 `main` 함수에서 코루틴을 실행하고 끝날 때까지 프로그램을 살려 둘 때 씁니다. 이 문서의 예제들이 그렇습니다. 단위 테스트에서도 쓸 수 있지만, 지금은 `kotlinx-coroutines-test`의 `runTest`를 더 많이 씁니다. `runTest`는 가상 시간을 써서 `delay`를 실제로 기다리지 않고 건너뜁니다.

```kotlin
// RunTestVirtualTime.kt (kotlinx-coroutines-test 1.11.0 필요)
@file:OptIn(ExperimentalCoroutinesApi::class)   // currentTime 이 실험 API 입니다

import kotlinx.coroutines.*
import kotlinx.coroutines.test.*
import kotlin.system.measureTimeMillis

suspend fun loadWithRetry(): String {
    delay(10_000)   // 10초 뒤 재시도한다고 칩니다
    return "성공"
}

fun main() {
    val real = measureTimeMillis {
        runTest {
            val result = loadWithRetry()
            println("결과=$result, 가상 시간=${currentTime}ms")
        }
    }
    println("실제로 걸린 시간: ${real}ms")
}
```

```text
결과=성공, 가상 시간=10000ms
실제로 걸린 시간: 58ms
```

코드 안에서는 10초가 지났지만 실제로는 0.1초도 걸리지 않았습니다(실제 걸린 시간은 실행마다 조금씩 다릅니다). `runBlocking`이었다면 테스트 하나에 10초가 걸립니다.

**막아도 되는 백그라운드 스레드.** 동기 결과를 요구하는 일반 API를 `suspend` 함수로 구현해야 할 때 씁니다. 예를 들어 OkHttp의 `Authenticator`나 `Interceptor`는 일반 함수이고, 비동기 요청(`enqueue`)이면 OkHttp의 작업 스레드에서 불립니다. 그 안에서 `suspend` 함수로 된 토큰 갱신을 불러야 하면 `runBlocking`으로 감쌀 수밖에 없고, 어차피 그 스레드는 응답을 기다리는 동안 막히는 스레드라 문제가 되지 않습니다. 토큰 갱신 방식 자체는 [OkHttp Authenticator vs Interceptor](Details-OkHttp-Authenticator-vs-Interceptor.md)에서 다룹니다.

**코루틴 안에서는 쓰지 않습니다.** 이미 코루틴 안이라면 기다리는 방법은 `join()`, `await()`, `withContext`처럼 `suspend` 함수로 된 것을 씁니다. 이들은 코루틴만 일시 중단하고 스레드는 놓아주므로 위의 두 문제가 생기지 않습니다. 코루틴 안에서 `runBlocking`을 쓸 이유는 사실상 없습니다.

더 자세한 사례는 [Exercise Caution When Using runBlocking on Android](https://medium.com/proandroiddev/exercise-caution-when-using-runblocking-on-android-e335796f869e)를 참고하면 좋습니다.

## 요약 {#summary}

`runBlocking`은 부른 스레드(`Thread.currentThread()`)를 기억해 두고, 코루틴과 자식이 모두 끝날 때까지 그 스레드에서 이벤트 루프를 돌리거나 스레드를 재우며 기다립니다. 부모가 없는 최상위 코루틴이라 바깥 코루틴이 취소돼도 함께 취소되지 않습니다.

스레드를 막기 때문에 메인 스레드에서 부르면 그동안 다른 코루틴이 그 스레드를 쓰지 못해 화면이 멈추고, 안에서 같은 스레드로 돌아오려 하면 교착 상태가 됩니다. `main` 함수, 테스트(가능하면 `runTest`), 막혀도 되는 백그라운드 스레드에서 일반 API를 구현할 때만 쓰고, 코루틴 안에서는 `join()`·`await()`·`withContext` 같은 `suspend` 함수로 기다립니다.
