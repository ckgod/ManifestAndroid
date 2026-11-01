# Q32) Continuation과 suspend 함수의 내부 동작

Q31에서 코루틴을 콜백 방식과 비교했습니다. 콜백 방식은 "결과가 오면 할 나머지 일"을 람다로 떼어 넘기고, 코루틴은 그 나머지를 적힌 순서대로 씁니다. 그 차이를 메우는 것이 컴파일러입니다. 컴파일러는 `suspend` 함수를 컴파일할 때 "나머지 할 일"을 담는 객체를 대신 만들어 넘기는데, 이 객체가 `Continuation`입니다.

이 토픽에서는 `Continuation`이 무엇인지, 컴파일러가 `suspend` 함수를 어떤 모양으로 바꾸는지, 그리고 일시 중단과 재개가 실제로 어떤 호출로 이루어지는지를 봅니다. 예제는 Kotlin 2.4.21, kotlinx-coroutines 1.11.0, JDK 25에서 실행했고, 바이트코드는 `javap`로 확인했습니다.

## Continuation 인터페이스 {#continuation-interface}

`Continuation`은 표준 라이브러리에 있는 작은 인터페이스입니다.

```kotlin
// Continuation.kt (kotlin-stdlib 2.4.21)
public interface Continuation<in T> {
    public val context: CoroutineContext
    public fun resumeWith(result: Result<T>)
}
```

- `context`: 이 코루틴의 `CoroutineContext`입니다. 어느 스레드에서 이어 갈지 정하는 디스패처, 코루틴의 수명을 나타내는 `Job` 같은 정보가 들어 있습니다.
- `resumeWith(result)`: 코루틴을 재개할 때 부르는 메서드입니다. 기다리던 작업의 결과를 `Result<T>`에 담아 넘깁니다. 성공이면 값이, 실패면 예외가 들어 있습니다.

보통은 `resumeWith`를 직접 부르지 않고 확장 함수 `resume(value)`와 `resumeWithException(exception)`을 씁니다. 각각 `resumeWith(Result.success(value))`, `resumeWith(Result.failure(exception))`과 같습니다.

생김새만 보면 결과 하나를 받는 콜백 인터페이스입니다. 실제로 그렇게 이해해도 됩니다. 다만 람다를 사람이 직접 쓰는 대신 컴파일러가 만들고, 그 안에 "어디까지 실행했는지"와 "그때 지역 변수 값"이 함께 들어 있다는 점이 다릅니다. 용어 자체의 정의는 [코루틴 용어 정리](Details-코루틴-용어-정리.md#continuation)에 있습니다.

## Continuation을 직접 잡아 재개하기 {#manual-resume}

`Continuation`이 하는 일은 직접 붙잡아 보면 가장 잘 보입니다. 표준 라이브러리의 `suspendCoroutine`은 현재 코루틴의 `Continuation`을 람다로 넘겨주고 코루틴을 일시 중단합니다. 아래 예제는 그 `Continuation`을 전역 변수에 저장해 두었다가, 응답이 도착한 척 `main`에서 직접 `resume`을 부릅니다. `kotlinx.coroutines` 없이 표준 라이브러리만 씁니다.

```kotlin
// FetchUser.kt
import kotlin.coroutines.*

class Profile(val name: String)
class User(val profile: Profile, val friends: List<String>)

var saved: Continuation<Any?>? = null

suspend fun fetchProfile(id: String): Profile = suspendCoroutine { cont ->
    println("  fetchProfile: 응답 기다리며 일시 중단")
    saved = cont as Continuation<Any?>
}

suspend fun fetchFriends(id: String): List<String> = suspendCoroutine { cont ->
    println("  fetchFriends: 응답 기다리며 일시 중단")
    saved = cont as Continuation<Any?>
}

suspend fun fetchUser(id: String): User {
    val profile = fetchProfile(id)   // 일시 중단 지점 1
    val friends = fetchFriends(id)   // 일시 중단 지점 2
    return User(profile, friends)
}

fun main() {
    suspend { fetchUser("ckgod") }.startCoroutine(Continuation(EmptyCoroutineContext) { r ->
        println("완료: ${r.getOrNull()?.profile?.name}, ${r.getOrNull()?.friends}")
    })
    println("startCoroutine 반환")
    println("프로필 응답 도착 → resume")
    saved!!.resume(Profile("ckgod"))
    println("resume 반환")
    println("친구 응답 도착 → resume")
    saved!!.resume(listOf("유진", "혜나"))
    println("resume 반환")
}
```

```text
  fetchProfile: 응답 기다리며 일시 중단
startCoroutine 반환
프로필 응답 도착 → resume
  fetchFriends: 응답 기다리며 일시 중단
resume 반환
친구 응답 도착 → resume
완료: ckgod, [유진, 혜나]
resume 반환
```

출력 순서에서 두 가지를 알 수 있습니다.

**일시 중단은 함수가 반환하는 것입니다.** `startCoroutine`은 코루틴을 시작해서 `fetchProfile`의 일시 중단 지점까지 실행한 뒤 바로 돌아왔습니다. 코루틴이 어딘가에서 스레드를 붙잡고 기다린 것이 아닙니다. `fetchUser`가 끝나지 않은 채로 반환했고, 이어서 할 일은 `saved`에 들어 있는 객체에 남았습니다.

**재개는 그 객체의 메서드를 부르는 것입니다.** `saved!!.resume(...)`을 부르자 `fetchUser`가 `fetchProfile` 다음 줄부터 이어서 실행되었습니다. 앞에서 받은 `id`도 그대로 남아 있어서 `fetchFriends(id)`를 불렀습니다. 그리고 다음 일시 중단 지점에서 또 반환해서 `resume 반환`이 찍혔습니다. 두 번째 `resume`에서는 끝까지 실행되어 `User`를 만들었고, 그 결과가 `startCoroutine`에 넘긴 완료용 `Continuation`으로 전달되어 `완료:` 줄이 찍혔습니다.

`resume`을 부른 `main` 스레드가 그대로 코루틴의 나머지를 실행한 점도 눈여겨볼 만합니다. 이 예제에는 디스패처가 없기 때문입니다. 디스패처가 있으면 달라지는데, 이건 아래 [재개되는 스레드와 디스패처](#dispatcher)에서 봅니다.

## 컴파일러의 CPS 변환 {#cps-transformation}

컴파일러가 `suspend` 함수에 하는 일을 CPS 변환이라고 부릅니다. CPS(Continuation-Passing Style)는 함수가 결과를 반환하는 대신, "결과를 받아서 나머지 일을 할 함수"를 인자로 받아 거기에 결과를 넘기는 코드 작성 방식입니다. 콜백 방식이 바로 CPS입니다.

컴파일러는 먼저 함수 시그니처를 바꿉니다. `suspend` 수정자가 사라지고, 마지막 파라미터로 `Continuation`이 붙고, 반환 타입은 `Object`가 됩니다. `javap`로 본 실제 시그니처는 이렇습니다.

```text
// 소스
suspend fun fetchUser(id: String): User

// 바이트코드 (javap)
public static final java.lang.Object fetchUser(java.lang.String, kotlin.coroutines.Continuation<? super User>);
```

Q31에서 `suspend` 함수를 일반 함수에서 부를 수 없는 이유가 여기 있습니다. 일반 함수에는 마지막 인자로 넘겨줄 `Continuation`이 없습니다.

반환 타입이 `User`가 아니라 `Object`인 이유는 이 함수가 두 종류의 값을 돌려줄 수 있기 때문입니다.

- 기다릴 일 없이 끝까지 실행되었으면 결과 값(`User`)을 그대로 돌려줍니다.
- 실제로 일시 중단되었으면 `COROUTINE_SUSPENDED`라는 특별한 표시 객체를 돌려줍니다. "아직 결과가 없고, 나중에 `Continuation`으로 알려 주겠다"는 뜻입니다.

`suspend` 함수 참조를 컴파일된 모양의 함수 타입으로 캐스팅하면 이 반환값을 직접 볼 수 있습니다.

```kotlin
// Marker.kt
import kotlin.coroutines.*

var saved: Continuation<String>? = null

suspend fun load(cached: Boolean): String {
    if (cached) return "캐시 값"            // 기다릴 일 없음
    return suspendCoroutine { saved = it }  // 실제로 멈춤
}

fun main() {
    val done = Continuation<String>(EmptyCoroutineContext) { println("완료: ${it.getOrNull()}") }
    // suspend 함수를 컴파일된 모양 그대로 불러 봅니다: (인자, Continuation) -> Any?
    val raw = ::load as (Boolean, Continuation<String>) -> Any?

    println("반환값 1: ${raw(true, done)}")
    println("반환값 2: ${raw(false, done)}")
    saved!!.resume("네트워크 값")
}
```

```text
반환값 1: 캐시 값
반환값 2: COROUTINE_SUSPENDED
완료: 네트워크 값
```

같은 함수가 캐시가 있을 때는 값을 바로 돌려주고, 없을 때는 `COROUTINE_SUSPENDED`를 돌려줬습니다. 두 번째 경우의 실제 결과는 나중에 `resume`을 불렀을 때 `done`으로 전달되었습니다. `suspend` 함수를 부른다고 항상 멈추는 것이 아니라, 끝까지 내려가서 정말 기다릴 일이 생겼을 때만 멈춘다는 뜻입니다.

## 상태 머신 {#state-machine}

시그니처만 바꿔서는 부족합니다. `fetchUser`는 일시 중단될 때마다 반환했다가, 재개될 때 처음이 아니라 멈춘 자리부터 다시 실행되어야 합니다. 그래서 컴파일러는 함수 본문을 상태 머신(state machine)으로 바꿉니다. 상태 머신은 "지금 몇 번째 단계인지"를 값으로 들고 있다가, 그 값에 따라 해당 단계의 코드로 바로 들어가는 구조입니다.

`fetchUser`를 컴파일하면 이 상태를 담는 클래스가 따로 생깁니다.

```text
// javap -p 'FetchUserKt$fetchUser$1'
final class FetchUserKt$fetchUser$1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
  java.lang.Object L$0;      // id
  java.lang.Object L$1;      // profile
  java.lang.Object result;   // 재개될 때 받은 결과
  int label;                 // 다음에 이어 갈 위치
  FetchUserKt$fetchUser$1(kotlin.coroutines.Continuation<? super FetchUserKt$fetchUser$1>);
  public final java.lang.Object invokeSuspend(java.lang.Object);
}
```

이 클래스가 `fetchUser` 한 번의 호출을 위한 `Continuation`입니다.

- `label`은 다음에 어느 일시 중단 지점 뒤에서 이어 갈지를 나타냅니다. 0이면 처음부터, 1이면 `fetchProfile` 다음부터, 2면 `fetchFriends` 다음부터입니다.
- `L$0`, `L$1`은 일시 중단 지점을 넘어서도 써야 하는 지역 변수를 담아 두는 칸입니다. `id`는 `fetchFriends(id)`에서, `profile`은 `User(profile, friends)`에서 다시 쓰이므로 저장됩니다. 일반 함수라면 이 값들은 스레드의 스택에 있다가 함수가 반환하면 사라지지만, 여기서는 힙에 있는 객체에 옮겨 두므로 반환한 뒤에도 남습니다.
- `result`는 재개될 때 `resumeWith`로 받은 결과를 잠시 보관합니다.

`fetchUser` 본문은 이 객체를 쓰도록 바뀝니다. 바이트코드를 자바 코드로 옮기면 다음과 같습니다. 읽기 쉽게 간추렸지만 분기 구조와 필드 이름은 실제 바이트코드 그대로입니다.

```java
// FetchUser 바이트코드를 자바로 옮긴 것 (간추림)
static Object fetchUser(String id, Continuation completion) {
    // 1. 재개 중이면 받은 상태 객체를 쓰고, 처음 호출이면 새로 만든다
    FetchUserKt$fetchUser$1 sm;
    if (completion instanceof FetchUserKt$fetchUser$1
            && (((FetchUserKt$fetchUser$1) completion).label & Integer.MIN_VALUE) != 0) {
        sm = (FetchUserKt$fetchUser$1) completion;
        sm.label -= Integer.MIN_VALUE;
    } else {
        sm = new FetchUserKt$fetchUser$1(completion);   // completion = 나를 부른 쪽
    }
    Object result = sm.result;
    Object SUSPENDED = IntrinsicsKt.getCOROUTINE_SUSPENDED();
    Object profile, friends;

    switch (sm.label) {
        case 0:
            ResultKt.throwOnFailure(result);
            sm.L$0 = id;                       // 일시 중단 전에 지역 변수 저장
            sm.label = 1;                      // 재개되면 case 1로
            profile = fetchProfile(id, sm);    // 자기 자신을 Continuation으로 넘김
            if (profile == SUSPENDED) return SUSPENDED;
            break;                             // 바로 결과가 왔으면 아래로 계속
        case 1:
            id = (String) sm.L$0;              // 저장해 둔 지역 변수 복원
            ResultKt.throwOnFailure(result);   // 실패로 재개됐으면 여기서 예외
            profile = result;
            break;
        case 2:
            profile = sm.L$1;
            id = (String) sm.L$0;
            ResultKt.throwOnFailure(result);
            friends = result;
            return new User((Profile) profile, (List) friends);
        default:
            throw new IllegalStateException("call to 'resume' before 'invoke' with coroutine");
    }

    // fetchProfile 이후 (case 0에서 바로 오거나 case 1에서 옴)
    sm.L$1 = profile;
    sm.label = 2;
    friends = fetchFriends(id, sm);
    if (friends == SUSPENDED) return SUSPENDED;
    return new User((Profile) profile, (List) friends);
}
```

상태 클래스의 `invokeSuspend`는 받은 결과를 `result`에 넣고 `fetchUser`를 다시 부르는 일만 합니다.

```java
// FetchUserKt$fetchUser$1.invokeSuspend (바이트코드를 자바로 옮긴 것)
public final Object invokeSuspend(Object result) {
    this.result = result;
    this.label |= Integer.MIN_VALUE;          // "재개 중" 표시
    return FetchUserKt.fetchUser(null, this); // id 는 상태 객체에서 복원하므로 null
}
```

처음 호출과 재개를 차례로 따라가면 이렇습니다.

1. **처음 호출.** 넘어온 `completion`은 `fetchUser`를 부른 쪽의 `Continuation`이므로 새 상태 객체를 만듭니다. `label`이 0이라 `case 0`에서 `id`를 저장하고 `label`을 1로 바꾼 뒤 `fetchProfile(id, sm)`을 부릅니다. `fetchProfile`이 `COROUTINE_SUSPENDED`를 돌려주면 `fetchUser`도 그대로 `COROUTINE_SUSPENDED`를 돌려주며 빠져나갑니다. 이 표시는 호출한 쪽으로 계속 전달되어, 앞 예제에서는 `startCoroutine`까지 돌아갔습니다.
2. **재개.** 누군가 `sm.resumeWith(결과)`를 부르면 `invokeSuspend`를 거쳐 `fetchUser(null, sm)`이 다시 호출됩니다. 이번에는 넘어온 객체에 "재개 중" 표시가 있으므로 새로 만들지 않고 그대로 씁니다. `label`이 1이라 `case 1`로 들어가 `id`를 복원하고, 받은 결과를 `profile`로 쓰고, `fetchFriends`를 부릅니다.

`fetchProfile`이 일시 중단하지 않고 값을 바로 돌려준 경우에는 `return` 없이 그다음 코드로 그대로 이어집니다. 앞의 `Marker.kt`처럼 기다릴 일이 없으면 상태 머신 안에서도 멈추지 않고 이어서 실행된다는 뜻입니다.

`label`의 가장 높은 비트(`Integer.MIN_VALUE`)는 "재개 중"을 표시합니다. 이 표시가 필요한 이유는 재귀 호출 때문입니다. `fetchUser`가 자기 자신을 부르면, 안쪽 호출에 넘어오는 `completion`은 바깥 `fetchUser`의 상태 객체이고 타입도 같습니다. 타입만 보고 재사용하면 바깥 호출의 상태를 덮어쓰게 되므로, 표시가 있을 때만 "나를 재개하는 중"으로 보고 재사용합니다. 책은 이 줄에 "시작됨으로 표시"라는 주석을 달았는데, 실제 의미는 재개 표시입니다.

책의 개념 코드는 `while (true)` 루프 안에 `switch`를 둔 모양이지만, 실제 바이트코드에는 루프가 없습니다. 값이 바로 오면 다음 단계 코드로 넘어가고, 일시 중단되면 반환하는 분기만 있습니다. 흐름을 이해하는 데에는 어느 쪽으로 봐도 차이가 없습니다.

## 재개 과정과 Continuation 사슬 {#resume-chain}

상태 객체를 만들 때 넘긴 `completion`은 `fetchUser`를 부른 쪽의 `Continuation`입니다. 상태 객체마다 자기를 부른 쪽을 가리키고 있으므로, `suspend` 함수가 여러 겹으로 호출되면 `Continuation`이 사슬처럼 이어집니다. 일반 함수에서 호출 스택이 하던 "다 끝나면 어디로 돌아갈지"를 이 사슬이 대신 기억합니다.

사슬은 표준 라이브러리의 `CoroutineStackFrame`으로 따라가 볼 수 있습니다. 디버거가 코루틴의 호출 경로를 보여 줄 때 쓰는 인터페이스입니다.

```kotlin
// Chain.kt
import kotlin.coroutines.*
import kotlin.coroutines.intrinsics.*
import kotlin.coroutines.jvm.internal.CoroutineStackFrame

suspend fun inner(): Int = suspendCoroutineUninterceptedOrReturn { cont ->
    var frame: CoroutineStackFrame? = cont as CoroutineStackFrame
    while (frame != null) {
        println("  $frame")
        frame = frame.callerFrame
    }
    1   // 일시 중단하지 않고 값을 바로 돌려줍니다
}
suspend fun middle(): Int = inner() + 1
suspend fun outer(): Int = middle() + 1

fun main() {
    suspend { outer() }.startCoroutine(Continuation(EmptyCoroutineContext) { println("결과: ${it.getOrNull()}") })
}
```

```text
  Continuation at ChainKt.middle(Chain.kt:14)
  Continuation at ChainKt.outer(Chain.kt:15)
  Continuation at ChainKt$main$1.invokeSuspend(Chain.kt:18)
결과: 3
```

`inner`가 받은 `Continuation`은 `middle`의 상태 객체이고, 그 위로 `outer`, `main`의 `suspend` 람다가 이어집니다. 사슬의 맨 끝에는 `startCoroutine`에 넘긴 완료용 `Continuation`이 있습니다.

`inner` 자신의 상태 객체는 없습니다. 실제로 컴파일 결과에도 `ChainKt$middle$1`, `ChainKt$outer$1`만 있고 `inner`용 클래스는 생기지 않습니다. `inner`처럼 마지막에 `suspend` 함수 하나를 부르고 그 결과를 그대로 반환하는 함수는, 재개된 뒤에 할 일이 없으므로 받은 `Continuation`을 그대로 넘기기만 하면 되기 때문입니다.

재개할 때 이 사슬을 거슬러 올라가는 일은 모든 상태 객체의 부모 클래스인 `BaseContinuationImpl`이 맡습니다.

```kotlin
// ContinuationImpl.kt (kotlin-stdlib 2.4.21, 디버깅용 호출과 주석 생략)
internal abstract class BaseContinuationImpl(
    public val completion: Continuation<Any?>?
) : Continuation<Any?>, CoroutineStackFrame, Serializable {

    public final override fun resumeWith(result: Result<Any?>) {
        var current = this
        var param = result
        while (true) {
            with(current) {
                val completion = completion!!
                val outcome: Result<Any?> =
                    try {
                        val outcome = invokeSuspend(param)
                        if (outcome === COROUTINE_SUSPENDED) return
                        Result.success(outcome)
                    } catch (exception: Throwable) {
                        Result.failure(exception)
                    }
                releaseIntercepted()
                if (completion is BaseContinuationImpl) {
                    current = completion
                    param = outcome
                } else {
                    completion.resumeWith(outcome)
                    return
                }
            }
        }
    }

    protected abstract fun invokeSuspend(result: Result<Any?>): Any?
}
```

1. 자기 `invokeSuspend`를 불러 멈춘 자리부터 실행합니다.
2. 도중에 다시 일시 중단되면(`COROUTINE_SUSPENDED`) 그대로 반환합니다. `resume`을 부른 쪽도 여기서 돌아갑니다.
3. 끝까지 실행되어 결과가 나오면 그 결과를 들고 `completion`, 즉 자기를 부른 쪽으로 올라가 같은 일을 반복합니다. 예외가 났으면 `Result.failure`로 담아 올립니다.
4. 사슬 끝의 완료용 `Continuation`에 닿으면 결과를 넘기고 끝납니다.

부른 쪽을 재개할 때 `completion.resumeWith`를 재귀로 부르지 않고 반복문으로 올라가므로, 사슬이 길어도 스레드 스택이 그만큼 깊어지지 않습니다.

앞의 `FetchUser.kt` 출력을 이 흐름으로 다시 읽으면 이렇습니다. 첫 번째 `resume(Profile)`은 `fetchUser`의 상태 객체를 재개했고, `fetchFriends`에서 다시 일시 중단되어 2번에서 반환했습니다. 그래서 `resume 반환`이 바로 찍혔습니다. 두 번째 `resume`에서는 `fetchUser`가 `User`를 반환했으므로 3번에 따라 `main`의 `suspend` 람다로 올라갔고, 람다도 끝나서 4번에 따라 완료용 `Continuation`이 `완료:`를 찍었습니다.

## 재개되는 스레드와 디스패처 {#dispatcher}

`resume`을 부르는 쪽은 기다리던 결과를 가진 쪽입니다. 네트워크 응답이 콜백으로 온다면 그 콜백이 실행되는 스레드가 `resume`을 부릅니다. 그러면 코루틴의 나머지도 그 스레드에서 실행될까요? 디스패처가 있느냐에 따라 다릅니다.

```kotlin
// Resume.kt
import kotlin.concurrent.thread
import kotlin.coroutines.*
import kotlinx.coroutines.runBlocking

fun t() = Thread.currentThread().name

// 콜백 API를 suspend 함수로 감쌉니다. 응답은 "network" 스레드에서 옵니다
suspend fun fetch(): String = suspendCoroutine { cont ->
    thread(name = "network") {
        Thread.sleep(100)
        println("  resume 호출 [${t()}]")
        cont.resume("응답")
    }
}

fun main() {
    println("1) 디스패처 없음")
    suspend {
        val r = fetch()
        println("  $r 이후 코드 [${t()}]")
    }.startCoroutine(Continuation(EmptyCoroutineContext) {})
    Thread.sleep(300)

    println("2) runBlocking 안")
    runBlocking {
        val r = fetch()
        println("  $r 이후 코드 [${t()}]")
    }
}
```

```text
1) 디스패처 없음
  resume 호출 [network]
  응답 이후 코드 [network]
2) runBlocking 안
  resume 호출 [network]
  응답 이후 코드 [main]
```

두 경우 모두 `resume`은 `network` 스레드에서 불렸습니다. 그런데 디스패처가 없는 1번은 나머지 코드도 `network` 스레드에서 실행되었고, `runBlocking` 안인 2번은 `main` 스레드로 돌아왔습니다.

차이는 `suspendCoroutine`이 넘겨주는 `Continuation`에 있습니다.

```kotlin
// Continuation.kt (kotlin-stdlib 2.4.21)
public suspend inline fun <T> suspendCoroutine(crossinline block: (Continuation<T>) -> Unit): T {
    contract { callsInPlace(block, InvocationKind.EXACTLY_ONCE) }
    return suspendCoroutineUninterceptedOrReturn { c: Continuation<T> ->
        val safe = SafeContinuation(c.intercepted())
        block(safe)
        safe.getOrThrow()
    }
}
```

`c.intercepted()`는 코루틴 컨텍스트에 디스패처가 있으면 `Continuation`을 디스패처로 한 번 감쌉니다. 감싼 `Continuation`의 `resume`을 부르면 바로 이어서 실행하지 않고, 디스패처에게 "이 코루틴의 나머지를 실행해 달라"고 맡깁니다. 디스패처는 자기가 관리하는 스레드에서 원래 상태 객체의 `resumeWith`를 부릅니다. `runBlocking`의 디스패처는 자기를 부른 스레드(`main`)에서 돌기 때문에 나머지가 `main`에서 실행되었습니다. 1번은 컨텍스트가 비어 있어 감쌀 것이 없으므로, `resume`을 부른 스레드에서 그대로 이어졌습니다.

책은 "dispatcher가 `sm.resumeWith(result)`를 호출합니다"라고 적었는데, 정확히는 결과를 가진 쪽이 `resume`을 부르고, 디스패처는 나머지를 어느 스레드에서 실행할지 정해 그 스레드에서 이어 갑니다. 안드로이드에서 `Dispatchers.Main`으로 시작한 코루틴이 네트워크 응답을 받은 뒤에도 메인 스레드에서 화면을 갱신할 수 있는 것이 이 구조 덕분입니다.

`suspendCoroutine`은 넘겨준 `Continuation`을 `SafeContinuation`으로 한 번 더 감쌉니다. 같은 `Continuation`을 두 번 재개하면 `IllegalStateException("Already resumed")`를 던지고, `block` 안에서 곧바로 `resume`을 불러도 일시 중단 없이 값을 돌려받도록 처리해 줍니다.

## 예외 전달 {#exception}

`resumeWith`가 `Result`를 받으므로 예외도 같은 길로 전달됩니다. 결과 대신 예외로 재개하면, 상태 머신의 `throwOnFailure(result)`가 일시 중단 지점에서 그 예외를 던집니다.

```kotlin
// Fail.kt
import kotlin.coroutines.*

var saved: Continuation<String>? = null
suspend fun fetch(): String = suspendCoroutine { saved = it }

fun main() {
    suspend {
        try { fetch() } catch (e: IllegalStateException) { println("잡음: ${e.message}") }
    }.startCoroutine(Continuation(EmptyCoroutineContext) {})
    saved!!.resumeWithException(IllegalStateException("서버 오류"))
}
```

```text
잡음: 서버 오류
```

예외는 `main`에서 `resumeWithException`을 부를 때 넘어왔지만, 코루틴 안에서는 `fetch()`를 부른 자리에서 던져진 것처럼 보여서 둘러싼 `try`/`catch`에 잡혔습니다. Q31에서 콜백 안의 예외는 바깥 `try`/`catch`로 잡을 수 없었던 것과 대비됩니다. 코루틴 안에서 잡지 않은 예외는 앞에서 본 `BaseContinuationImpl`이 `Result.failure`로 담아 부른 쪽으로 올려 보냅니다.

## 요약 {#summary}

`Continuation`은 `context`와 `resumeWith(Result<T>)` 하나를 가진 인터페이스로, 일시 중단된 코루틴의 "나머지 할 일"과 그때의 지역 변수를 담은 객체입니다. 컴파일러는 `suspend` 함수에 `Continuation` 파라미터를 붙이고 반환 타입을 `Object`로 바꿉니다. 함수는 끝까지 실행되면 결과 값을, 실제로 일시 중단되면 `COROUTINE_SUSPENDED`를 돌려줍니다.

함수 본문은 `label`과 지역 변수 칸(`L$0`, `L$1` …)을 가진 상태 객체를 쓰는 상태 머신으로 바뀝니다. 일시 중단은 이 객체에 상태를 저장하고 `COROUTINE_SUSPENDED`를 반환하는 것이고, 재개는 누군가 이 객체의 `resumeWith`를 불러 `label`이 가리키는 자리부터 다시 실행하는 것입니다. 상태 객체는 자기를 부른 쪽의 `Continuation`(`completion`)을 들고 있어 사슬을 이루고, 끝까지 실행되면 결과를 들고 이 사슬을 거슬러 올라갑니다.

`resume`은 결과를 가진 쪽이 부르고, 컨텍스트에 디스패처가 있으면 나머지 실행은 디스패처가 정한 스레드로 넘어갑니다. 예외도 `Result.failure`로 같은 길을 따라 전달되어 일시 중단 지점에서 던져지므로 `try`/`catch`로 잡을 수 있습니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Continuation은 무엇이고, 콜백과 어떤 관계인가요?">

`Continuation`은 일시 중단된 코루틴이 재개될 때 할 "나머지 일"을 담은 객체입니다. `resumeWith(Result<T>)` 메서드 하나로 결과나 예외를 받아 멈춘 자리부터 실행을 이어 갑니다.

결과 하나를 받는 콜백과 구조가 같습니다. 차이는 콜백 방식에서는 나머지 일을 사람이 람다로 떼어 넘기지만, 코루틴에서는 컴파일러가 `suspend` 함수 본문으로부터 이 객체를 만들어 넘긴다는 점입니다. 그래서 코드는 순서대로 쓰면서도 실행은 콜백처럼 나뉘어 이루어집니다.

</def>
<def title="Q) 컴파일러는 suspend 함수의 시그니처를 어떻게 바꾸나요? 반환 타입이 Object가 되는 이유는 무엇인가요?">

`suspend` 수정자를 없애고 마지막 파라미터로 `Continuation`을 붙이며, 반환 타입을 `Object`로 바꿉니다. `suspend fun fetchUser(id: String): User`는 `Object fetchUser(String, Continuation<? super User>)`가 됩니다.

반환 타입이 `Object`인 이유는 두 종류의 값을 돌려줄 수 있어야 하기 때문입니다. 기다릴 일 없이 끝나면 결과 값을 그대로 돌려주고, 실제로 일시 중단되면 `COROUTINE_SUSPENDED` 표시 객체를 돌려줍니다. 후자의 경우 실제 결과는 나중에 `Continuation`의 `resumeWith`로 전달됩니다.

</def>
<def title="Q) 상태 머신에서 label과 L$0 같은 필드는 무슨 역할을 하나요?">

`label`은 재개될 때 어느 일시 중단 지점 뒤부터 이어 갈지를 나타냅니다. 함수는 `switch (label)`로 해당 위치에 바로 들어갑니다. 일시 중단 지점에 들어가기 전에 `label`을 다음 값으로 바꿔 둡니다.

`L$0`, `L$1` 같은 필드는 일시 중단 지점을 넘어서도 쓰이는 지역 변수를 저장합니다. 일반 함수의 지역 변수는 스택에 있다가 반환하면 사라지지만, 일시 중단은 함수가 반환하는 것이므로 다시 쓸 값을 힙의 상태 객체에 옮겨 두고 재개할 때 복원합니다.

</def>
<def title="Q) suspend 함수를 호출하면 항상 일시 중단되나요?">

그렇지 않습니다. 호출을 따라 내려가다 실제로 기다릴 일이 생겨 `COROUTINE_SUSPENDED`를 돌려받았을 때만 일시 중단됩니다. 캐시된 값을 바로 돌려주는 경우처럼 기다릴 일이 없으면 결과 값이 그대로 반환되고, 상태 머신 안에서도 `return` 없이 다음 단계 코드로 이어집니다.

</def>
<def title="Q) 네트워크 콜백 스레드에서 resume을 불렀는데 나머지 코드가 메인 스레드에서 실행되는 이유는 무엇인가요?">

`suspendCoroutine`이 넘겨주는 `Continuation`이 `intercepted()`로 디스패처에 감싸져 있기 때문입니다. 감싼 `Continuation`의 `resume`을 부르면 즉시 실행하지 않고 디스패처에 나머지 실행을 맡기고, 디스패처는 자기 스레드에서 원래 상태 객체의 `resumeWith`를 부릅니다.

`runBlocking`이나 `Dispatchers.Main`처럼 특정 스레드에서 도는 디스패처면 그 스레드로 돌아옵니다. 컨텍스트에 디스패처가 없으면 감쌀 것이 없으므로 `resume`을 부른 스레드에서 그대로 이어집니다.

</def>
<def title="Q) 재개된 코루틴이 끝나면 호출한 함수로는 어떻게 돌아가나요?">

상태 객체는 만들어질 때 자기를 부른 쪽의 `Continuation`을 `completion`으로 받아 둡니다. `BaseContinuationImpl.resumeWith`는 자기 `invokeSuspend`가 결과를 내면 그 결과를 들고 `completion`으로 올라가 같은 일을 반복하고, 사슬 끝의 완료용 `Continuation`에 닿으면 결과를 넘기고 끝납니다.

일반 함수의 호출 스택이 하던 "끝나면 어디로 돌아갈지"를 이 `Continuation` 사슬이 대신합니다. 올라가는 과정은 재귀 호출이 아니라 반복문이라 사슬이 길어도 스레드 스택이 깊어지지 않습니다.

</def>
</deflist>
