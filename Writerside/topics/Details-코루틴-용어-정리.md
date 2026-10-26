# Details: 코루틴 용어 정리

코틀린 코루틴 설계 문서(KEEP의 [coroutines 제안서](https://github.com/Kotlin/KEEP/blob/master/proposals/coroutines.md))는 코루틴과 관련된 용어를 아래처럼 정의합니다. 이후 토픽에서 계속 나오는 말이라 한곳에 모아 둡니다.

## 코루틴 {#coroutine}

일시 중단할 수 있는 계산 하나를 실행한 것(인스턴스)입니다. 개념적으로는 스레드와 비슷해서, 코드 블록을 실행하고 만들어지고 시작되고 끝나는 수명이 있습니다. 다만 특정 스레드에 묶이지 않아서 한 스레드에서 일시 중단되었다가 다른 스레드에서 재개될 수 있습니다.

future나 promise처럼 결과 하나로 끝납니다. 결과는 값이거나 예외입니다. future는 나중에 채워질 결과를 읽기만 하는 자리이고, promise는 비동기 작업이 끝났을 때 결과를 써 넣을 수 있는 객체입니다.

## suspend 함수 {#suspending-function}

`suspend` 수정자가 붙은 함수입니다. 다른 `suspend` 함수를 불러서 현재 스레드를 막지 않고 실행을 일시 중단할 수 있습니다. 일반 코드에서는 부를 수 없고, 다른 `suspend` 함수나 `suspend` 람다 안에서만 부를 수 있습니다. `kotlinx.coroutines`의 `delay`, `Deferred.await`, 표준 라이브러리 `SequenceScope`의 `yield`가 라이브러리가 제공하는 `suspend` 함수의 예입니다.

## suspend 람다 {#suspending-lambda}

코루틴 안에서 실행되도록 만든 코드 블록입니다. 생김새는 일반 람다와 같지만 타입에 `suspend`가 붙어 있어서, 안에서 `suspend` 함수를 부를 수 있습니다. 이름 없는 `suspend` 함수를 만드는 문법이라고 보면 됩니다. `launch { }`, `async { }`, `sequence { }` 뒤의 블록이 모두 `suspend` 람다입니다.

일반 람다라도 `inline` 함수에 넘겨서 호출 자리에 펼쳐지는 람다라면 안에서 `suspend` 함수를 부를 수 있습니다. 펼쳐진 코드는 바깥 `suspend` 함수의 일부가 되기 때문입니다. 반대로 `noinline`이나 `crossinline` 람다는 다른 곳에서 나중에 실행될 수 있으므로 안에서 `suspend` 함수를 부를 수 없습니다.

```kotlin
// InlineSuspend.kt
inline fun runNoinline(noinline block: () -> Unit) = block()
inline fun runCrossinline(crossinline block: () -> Unit) = Runnable { block() }.run()

suspend fun inlineOk() {
    StringBuilder().apply { delay(1); append("ok") }   // 컴파일됨: apply 는 inline
}
suspend fun inNoinline() { runNoinline { delay(1) } }
// error: suspension functions can only be called within coroutine body.
suspend fun inCrossinline() { runCrossinline { delay(1) } }
// error: suspension functions can only be called within coroutine body.
```

KEEP 문서는 일시 중단을 Q16의 비지역 반환과 같은 종류로 봅니다. 둘 다 람다 안에서 바깥 함수의 흐름을 바꾸는 일이라, 비지역 반환이 허용되는 람다에서만 일시 중단도 허용됩니다.

## suspend 함수 타입 {#suspending-function-type}

`suspend` 함수나 `suspend` 람다의 타입입니다. 일반 함수 타입 앞에 `suspend`가 붙은 모양입니다. 예를 들어 `suspend () -> Int`는 인자 없이 `Int`를 돌려주는 `suspend` 함수의 타입입니다. `suspend fun foo(): Int`로 선언한 함수도 이 타입에 맞습니다.

## 코루틴 빌더 {#coroutine-builder}

`suspend` 람다를 받아서 코루틴을 만들고, 필요하면 결과를 꺼낼 수 있게 해 주는 함수입니다. `launch { }`, `async { }`는 `kotlinx.coroutines` 라이브러리에, `sequence { }`는 표준 라이브러리에 있습니다.

몇몇 언어는 코루틴을 `async`나 `generate` 같은 키워드로 언어에 넣었지만, 코틀린은 이것들을 컴파일러에 넣지 않고 평범한 함수로 만듭니다. 그래서 `launch`나 `async`도 일반 함수처럼 호출하고, 필요하면 같은 방식으로 새 빌더를 만들 수 있습니다.

## 일시 중단 지점 {#suspension-point}

코루틴 실행이 일시 중단될 수 있는 자리입니다. 문법상으로는 `suspend` 함수를 부르는 곳마다 일시 중단 지점이 됩니다. 다만 실제로 멈추는 것은 그 호출이 끝까지 내려가서 표준 라이브러리의 일시 중단 장치(`suspendCoroutine` 등)를 만났을 때입니다. `suspend` 함수를 불러도 그 안에서 기다릴 일이 없으면 멈추지 않고 그대로 이어서 실행됩니다.

## Continuation {#continuation}

일시 중단된 코루틴이 "이 다음에 할 일"을 담은 객체입니다. 일시 중단 지점 이후의 나머지 실행, 그리고 그때 필요한 지역 변수가 들어 있습니다. 코루틴은 일시 중단될 때마다 이 상태를 담아 두고, 재개될 때 여기서부터 이어 갑니다.

```kotlin
// Continuation.kt (kotlin-stdlib 2.4.21)
public interface Continuation<in T> {
    public val context: CoroutineContext
    public fun resumeWith(result: Result<T>)
}
```

`resumeWith`에 값이나 예외를 넘기면 마지막 일시 중단 지점의 결과로 그 값이 들어가면서 코루틴이 재개됩니다.

`sequence`로 보면 이렇습니다.

```kotlin
// SequenceContinuation.kt
sequence {
    for (i in 1..10) yield(i * i)
    println("over")
}
```

`yield`를 부를 때마다 코루틴은 값을 내놓고 일시 중단되며, "반복문의 다음 회차부터 이어 가기"를 담은 continuation이 남습니다. 다음 값을 요청받으면 그 continuation으로 재개합니다. 마지막 회차가 끝나면 `over`를 찍고 코루틴이 끝납니다.

만들어졌지만 아직 시작하지 않은 코루틴은 `Continuation<Unit>` 하나로 표현됩니다. 전체 실행을 처음부터 담은 continuation입니다. 표준 라이브러리의 저수준 함수 `createCoroutine`으로 직접 확인할 수 있습니다.

```kotlin
// CreateCoroutine.kt
import kotlin.coroutines.*

fun main() {
    val first: Continuation<Unit> = suspend {
        println("코루틴 시작")
        42
    }.createCoroutine(Continuation(EmptyCoroutineContext) { result ->
        println("완료: $result")
    })
    println("만들기만 함")
    first.resume(Unit)
}
```

```text
만들기만 함
코루틴 시작
완료: Success(42)
```

`createCoroutine`은 코루틴을 만들기만 하고 시작하지 않으므로 `만들기만 함`이 먼저 찍힙니다. 돌려받은 `Continuation<Unit>`에 `resume(Unit)`을 부르는 순간 코루틴이 처음부터 실행되고, 끝나면 넘겨준 완료용 continuation에 결과 `Success(42)`가 전달됩니다. `launch`나 `sequence` 같은 빌더도 결국 이런 저수준 함수 위에 만들어져 있습니다.

## 요약 {#summary}

코루틴은 일시 중단할 수 있는 계산의 인스턴스이고, 스레드에 묶이지 않으며 값이나 예외 하나로 끝납니다. 컴파일러가 직접 지원하는 것은 `suspend` 함수, `suspend` 람다, `suspend` 함수 타입뿐이고, 코루틴 빌더를 비롯한 나머지는 라이브러리 함수입니다. 일반 람다도 `inline`으로 펼쳐지는 경우에만 `suspend` 함수를 부를 수 있습니다.

일시 중단 지점은 `suspend` 함수를 부르는 곳이지만 실제로 멈추는 것은 일시 중단 장치를 만났을 때입니다. 멈출 때 남는 continuation은 이후의 실행과 필요한 상태를 담고 있으며, `resumeWith`로 재개됩니다. 아직 시작하지 않은 코루틴은 `Continuation<Unit>` 하나로 표현됩니다.
