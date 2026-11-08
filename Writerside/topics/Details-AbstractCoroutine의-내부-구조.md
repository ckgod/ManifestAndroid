# Details: AbstractCoroutine의 내부 구조

`launch`, `async`, `runBlocking`, `produce`, `actor`가 만드는 코루틴 객체는 모두 `AbstractCoroutine`을 상속합니다. 빌더마다 고쳐 쓰는 부분은 몇 줄뿐이고, 상태 관리·완료 처리·부모와의 연결 같은 공통 동작은 전부 이 클래스와 그 부모인 `JobSupport`에 들어 있습니다. 이 문서에서는 그 공통 동작을 봅니다.

예제는 Kotlin 2.4.21, kotlinx-coroutines 1.11.0, JDK 25에서 실행했고, 소스도 같은 버전에서 옮겼습니다.

## 세 가지 역할 {#three-roles}

```kotlin
// AbstractCoroutine.kt (kotlinx-coroutines 1.11.0)
public abstract class AbstractCoroutine<in T>(
    parentContext: CoroutineContext,
    initParentJob: Boolean,
    active: Boolean
) : JobSupport(active), Job, Continuation<T>, CoroutineScope
```

객체 하나가 세 인터페이스를 함께 구현합니다.

1. **`Job`.** `Job`의 구현인 `JobSupport`를 상속합니다. 자기 상태(시작 전, 실행 중, 완료 중, 완료 등)를 관리하고, 완료를 기다리는 쪽(리스너) 목록과 부모·자식 연결을 갖습니다. 빌더가 돌려주는 `Job`이 바로 이 객체입니다.
2. **`Continuation<T>`.** 코루틴 블록이 끝났을 때 결과를 받는 자리입니다. Q32에서 `suspend` 함수의 상태 객체들이 `completion`으로 이어진 사슬을 봤는데, 그 사슬의 맨 끝에 있는 "완료용 `Continuation`"이 이 객체입니다. 블록이 값을 내거나 예외를 던지면 그 결과가 이 객체의 `resumeWith`로 전달됩니다.
3. **`CoroutineScope`.** 블록 안의 `this`가 이 객체입니다. 이 스코프의 컨텍스트는 `parentContext + this`, 즉 부모 컨텍스트에 자기 자신을 `Job`으로 넣은 것입니다. 그래서 블록 안에서 `launch`를 부르면 새 코루틴은 이 객체를 부모로 삼습니다.

실제로 같은 객체인지 확인해 봤습니다.

```kotlin
// ThreeRoles.kt
import kotlinx.coroutines.*
import kotlin.coroutines.Continuation

fun main() = runBlocking<Unit> {
    var self: Any? = null
    val job = launch {
        self = this   // launch 블록의 this(CoroutineScope)를 밖으로 꺼내 둡니다
        println("Job 인가요? ${this is Job}")
        println("Continuation 인가요? ${(this as Any) is Continuation<*>}")
        println("컨텍스트의 Job 이 자기 자신인가요? ${this === coroutineContext[Job]}")
    }
    job.join()
    println("launch 가 돌려준 Job 과 같은 객체인가요? ${self === job}")
    println("클래스 이름: ${job::class.simpleName}")
}
```

```text
Job 인가요? true
Continuation 인가요? true
컨텍스트의 Job 이 자기 자신인가요? true
launch 가 돌려준 Job 과 같은 객체인가요? true
클래스 이름: StandaloneCoroutine
```

블록 안의 `this`, 컨텍스트에 든 `Job`, `launch`가 돌려준 `Job`이 모두 같은 `StandaloneCoroutine` 객체였습니다.

## 상태 머신 {#state-machine}

`JobSupport`는 코루틴의 상태를 `_state`라는 원자적(atomic) 필드 하나에 담습니다. 상태를 바꿀 때는 잠금(lock)을 쓰지 않고 CAS(compare-and-swap)를 씁니다. CAS는 "지금 값이 내가 읽은 값과 같을 때만 새 값으로 바꾼다"를 한 번에 처리하는 CPU 연산으로, 다른 스레드가 먼저 바꿨으면 실패하고 다시 읽어서 시도합니다. 이렇게 잠금 없이 동시 접근을 처리하는 방식을 lock-free라고 부릅니다.

`Job`의 상태와 바깥에서 보이는 값은 이렇습니다(`Job` 소스의 문서 주석에 있는 표입니다).

| 상태 | `isActive` | `isCompleted` | `isCancelled` | 뜻 |
|---|---|---|---|---|
| New | `false` | `false` | `false` | 만들었지만 시작 전 (`LAZY`일 때만) |
| Active | `true` | `false` | `false` | 실행 중 |
| Completing | `true` | `false` | `false` | 본문은 끝났고 자식을 기다리는 중 |
| Cancelling | `false` | `false` | `true` | 취소되었고 자식의 정리를 기다리는 중 |
| Cancelled | `false` | `true` | `true` | 취소로 끝남 (예외로 끝난 경우 포함) |
| Completed | `false` | `true` | `false` | 정상적으로 끝남 |

내부에서는 `_state`에 상태마다 다른 객체가 들어갑니다. 시작 전이면 `EMPTY_NEW`, 실행 중이면 `EMPTY_ACTIVE`나 리스너 목록(`NodeList`), 완료 중·취소 중이면 `Finishing`, 예외로 끝났으면 `CompletedExceptionally`, 정상 종료면 결과 값 그 자체입니다. Completing과 Cancelling은 같은 `Finishing` 객체를 쓰고, 취소 원인이 들어 있는지로 구분합니다.

중간 상태 두 개를 실행으로 확인해 봤습니다.

```kotlin
// JobStates.kt
import kotlinx.coroutines.*

fun Job.state(): String = "isActive=$isActive, isCompleted=$isCompleted, isCancelled=$isCancelled"

fun main() = runBlocking<Unit> {
    // 1. 본문은 끝났지만 자식이 남은 부모: Completing
    val parent = launch {
        launch { delay(200) }   // 자식
        println("부모 본문 끝")
    }
    delay(100)
    println("자식 기다리는 중: ${parent.state()}")
    parent.join()
    println("자식까지 끝남:   ${parent.state()}")

    // 2. 자식이 남은 상태에서 취소된 부모: Cancelling
    val cancelled = launch {
        launch {
            try {
                delay(1000)
            } finally {
                // 취소된 뒤 200ms 동안 정리 작업을 한다고 칩니다
                withContext(NonCancellable) { delay(200) }
            }
        }
    }
    delay(50)
    cancelled.cancel()
    println("취소 처리 중:   ${cancelled.state()}")
    cancelled.join()
    println("취소 완료:      ${cancelled.state()}")
}
```

```text
부모 본문 끝
자식 기다리는 중: isActive=true, isCompleted=false, isCancelled=false
자식까지 끝남:   isActive=false, isCompleted=true, isCancelled=false
취소 처리 중:   isActive=false, isCompleted=false, isCancelled=true
취소 완료:      isActive=false, isCompleted=true, isCancelled=true
```

부모의 본문은 바로 끝났지만 `isCompleted`는 자식이 끝난 뒤에야 `true`가 되었습니다. Completing은 바깥에서 보기에 Active와 값이 같아서, 부모가 아직 "실행 중"으로 보입니다. 이 Completing 단계가 있어서 부모는 항상 자식을 기다리고, `join()`도 자식까지 끝나야 돌아옵니다. 구조화된 동시성이 이 상태 전이로 이루어집니다.

## 완료 처리 {#resume-with}

블록이 끝나면 결과가 `resumeWith`로 들어옵니다. 이것이 `AbstractCoroutine`이 `Continuation`을 구현한 부분입니다.

```kotlin
// AbstractCoroutine.kt (kotlinx-coroutines 1.11.0)
public final override fun resumeWith(result: Result<T>) {
    val state = makeCompletingOnce(result.toState())
    if (state === COMPLETING_WAITING_CHILDREN) return
    afterResume(state)
}
```

1. `launch`나 `async`의 블록이 끝까지 실행되면, Q32에서 본 `BaseContinuationImpl.resumeWith`가 사슬 끝의 `completion`, 즉 이 코루틴 객체의 `resumeWith`를 부릅니다. 블록이 값을 냈으면 `Result.success(값)`, 예외를 던졌으면 `Result.failure(예외)`가 들어옵니다.
2. `result.toState()`가 결과를 상태 객체로 바꿉니다. 성공이면 값 그대로, 실패면 예외를 감싼 `CompletedExceptionally`가 됩니다.
3. `makeCompletingOnce`가 Completing 상태로 바꾸려고 시도합니다. 아직 실행 중인 자식이 있으면 `Finishing` 상태로 바꾸고 `COMPLETING_WAITING_CHILDREN`을 돌려주며, `resumeWith`는 여기서 그냥 돌아갑니다. 최종 상태는 마지막 자식이 끝날 때 그 자식 쪽에서 마무리합니다. 자식이 없으면 곧바로 최종 상태가 됩니다.
4. 최종 상태가 정해지면 등록된 완료 리스너를 모두 부릅니다. `join()`이나 `await()`로 기다리던 코루틴이 재개되는 것이 이 단계입니다. 이어서 완료 훅(`onCompleted`·`onCancelled`, `afterCompletion`)이 불립니다.

## 부모와 자식의 연결 {#parent-child}

부모·자식 관계는 코루틴 객체를 만들 때 맺어집니다. `AbstractCoroutine`의 초기화 블록이 `JobSupport`의 `initParentJob`을 부릅니다.

```kotlin
// AbstractCoroutine.kt
init {
    if (initParentJob) initParentJob(parentContext[Job])
}

// JobSupport.kt (일부 생략)
protected fun initParentJob(parent: Job?) {
    if (parent == null) {
        parentHandle = NonDisposableHandle   // 부모가 없는 최상위 코루틴
        return
    }
    parent.start()                           // 부모가 아직 시작 전이면 시작시킵니다
    val handle = parent.attachChild(this)    // 부모의 자식 목록에 자기를 등록합니다
    parentHandle = handle
    // ...
}
```

- 이어받은 컨텍스트에서 부모 `Job`을 찾습니다. `runBlocking`처럼 부모가 없으면 연결을 만들지 않습니다.
- `parent.attachChild(this)`로 부모에게 자기를 자식으로 등록하고, 연결 손잡이(`ChildHandle`)를 받아 둡니다.
- 이 연결을 따라 양쪽으로 신호가 갑니다. 부모가 취소되면 자식을 취소하고, 자식이 예외로 끝나면 이 손잡이로 부모에게 알립니다(`childCancelled`). 자식이 끝나면 연결을 풀어서, 끝난 자식의 `parent`는 `null`이 됩니다.

## 빌더별로 고쳐 쓰는 훅 {#hooks}

빌더마다 다른 동작은 `AbstractCoroutine`·`JobSupport`가 열어 둔 훅(정해진 시점에 불리는 함수) 몇 개를 고쳐 써서 만듭니다.

| 클래스 (빌더) | 고쳐 쓰는 훅 | 하는 일 |
|---|---|---|
| `StandaloneCoroutine` (`launch`) | `handleJobException` | 예외를 맡을 부모 코루틴이 없으면 `CoroutineExceptionHandler`나 스레드 기본 처리기에 보고합니다 |
| `DeferredCoroutine` (`async`) | 없음 (`await`만 추가) | 예외를 보고하지 않고 최종 상태에 보관했다가 `await()`에서 던집니다 |
| `ProducerCoroutine` (`produce`) | `onCompleted`, `onCancelled` | 코루틴이 끝나면 채널을 닫고, 실패면 원인을 담아 닫습니다 |
| `ActorCoroutine` (`actor`) | `onCancelling`, `handleJobException` | 취소되면 메일박스를 취소하고, 예외는 `launch`처럼 보고합니다 |
| `BlockingCoroutine` (`runBlocking`) | `afterCompletion` | 다른 스레드에서 끝났으면 막혀 있던 스레드를 깨웁니다(`unpark`) |

`launch`와 `async`의 예외 처리 차이가 이 표의 첫 두 줄에서 나옵니다. 자세한 내용은 [launch와 async의 차이](Details-launch와-async의-차이.md)에서 다룹니다.

## 요약 {#summary}

`AbstractCoroutine`은 객체 하나로 `Job`(상태와 부모·자식 관리), `Continuation`(블록의 결과를 받는 자리), `CoroutineScope`(블록의 `this`, 자식의 부모)를 겸합니다. 빌더가 돌려주는 핸들, 블록 안의 `this`, 컨텍스트의 `Job`이 모두 같은 객체입니다.

상태는 `JobSupport`의 원자적 필드 `_state` 하나에 담기고 CAS로 바뀝니다. 블록이 끝나면 `resumeWith`가 불리고, 자식이 남아 있으면 Completing에서 기다렸다가 마지막 자식이 끝날 때 최종 상태가 됩니다. 부모와의 연결은 객체를 만들 때 `initParentJob`이 `attachChild`로 맺습니다. 빌더마다 다른 예외 보고·채널 닫기·스레드 깨우기는 `handleJobException`, `onCompleted`, `onCancelled`, `afterCompletion` 같은 훅을 고쳐 써서 만듭니다.
