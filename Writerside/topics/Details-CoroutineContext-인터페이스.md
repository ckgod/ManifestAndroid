# Details: CoroutineContext 인터페이스

[Q35](Q35-coroutine-context.md)에서는 컨텍스트를 "키로 찾는 요소 묶음"으로 쓰는 법을 봤습니다. 이 문서에서는 그 묶음이 안에서 어떻게 만들어져 있는지 봅니다. `CoroutineContext`는 코루틴 라이브러리(kotlinx-coroutines)가 아니라 코틀린 표준 라이브러리의 `kotlin.coroutines` 패키지에 있는 인터페이스이고, 구현도 파일 두 개에 다 들어 있을 만큼 작습니다.

예제는 Kotlin 2.4.21, kotlinx-coroutines 1.11.0, JDK 25에서 실행했고, 소스도 같은 버전에서 옮겼습니다.

## 인터페이스의 모양 {#interface}

문서 주석을 걷어 내면 인터페이스는 이것이 전부입니다(`plus`의 본문은 아래 [plus의 동작](#plus)에서 봅니다).

```kotlin
// CoroutineContext.kt (Kotlin 2.4.21 표준 라이브러리, 주석 생략)
public interface CoroutineContext {
    public operator fun <E : Element> get(key: Key<E>): E?
    public fun <R> fold(initial: R, operation: (R, Element) -> R): R
    public operator fun plus(context: CoroutineContext): CoroutineContext = /* 아래에서 봅니다 */
    public fun minusKey(key: Key<*>): CoroutineContext

    public interface Key<E : Element>

    public interface Element : CoroutineContext {
        public val key: Key<*>

        public override operator fun <E : Element> get(key: Key<E>): E? =
            if (this.key == key) this as E else null

        public override fun <R> fold(initial: R, operation: (R, Element) -> R): R =
            operation(initial, this)

        public override fun minusKey(key: Key<*>): CoroutineContext =
            if (this.key == key) EmptyCoroutineContext else this
    }
}
```

연산은 넷입니다.

| 연산 | 하는 일 | 컬렉션에 빗대면 |
|---|---|---|
| `get(key)` | 그 키의 요소를 꺼냅니다. 없으면 `null`. `context[key]`로 씁니다 | `map[key]` |
| `fold(initial, operation)` | 요소를 앞에서부터 하나씩 훑으며 값을 누적합니다 | `list.fold` |
| `plus(context)` | 두 컨텍스트를 합친 새 컨텍스트를 만듭니다. 같은 키는 오른쪽이 이깁니다 | `map + otherMap` |
| `minusKey(key)` | 그 키의 요소만 뺀 새 컨텍스트를 만듭니다 | `map - key` |

`Key<E>`는 메서드가 하나도 없는 빈 인터페이스입니다. 객체의 정체(같은 객체인지)만 비교에 쓰이고, 타입 인자 `E`는 `get`의 결과 타입을 정하는 데만 쓰입니다.

`Element`가 `CoroutineContext`를 상속하고 세 연산의 기본 구현까지 갖고 있다는 점이 중요합니다. 요소 하나가 "요소가 하나뿐인 컨텍스트"로 완전히 동작하므로, 요소를 만들 때 키 하나만 정하면 나머지는 따로 구현할 필요가 없습니다. 표준 라이브러리의 `AbstractCoroutineContextElement`는 생성자로 받은 키를 `key` 프로퍼티로 내주는 것 말고는 아무것도 하지 않습니다.

```kotlin
// CoroutineContextImpl.kt
public abstract class AbstractCoroutineContextElement(public override val key: Key<*>) : Element
```

## 세 가지 구현 {#implementations}

`CoroutineContext`를 구현하는 것은 셋뿐입니다.

1. **요소(`Element`).** 요소가 하나인 컨텍스트입니다.
2. **`EmptyCoroutineContext`.** 요소가 하나도 없는 컨텍스트입니다. 빌더의 `context` 매개변수 기본값이 이것입니다.
3. **`CombinedContext`.** 요소가 둘 이상인 컨텍스트입니다. `internal` 클래스라 직접 만들 수 없고, `plus`가 만들어 줍니다.

`EmptyCoroutineContext`는 모든 연산이 "아무것도 없음"으로 끝납니다.

```kotlin
// CoroutineContextImpl.kt (일부)
public object EmptyCoroutineContext : CoroutineContext, Serializable {
    public override fun <E : Element> get(key: Key<E>): E? = null
    public override fun <R> fold(initial: R, operation: (R, Element) -> R): R = initial
    public override fun plus(context: CoroutineContext): CoroutineContext = context
    public override fun minusKey(key: Key<*>): CoroutineContext = this
}
```

## CombinedContext의 구조 {#combined-context}

`CombinedContext`는 필드가 둘입니다. 왼쪽(`left`)에는 나머지 컨텍스트가, 오른쪽(`element`)에는 요소 하나가 들어갑니다.

```kotlin
// CoroutineContextImpl.kt
// this is a left-biased list, so that `plus` works naturally
internal class CombinedContext(
    private val left: CoroutineContext,
    private val element: Element
) : CoroutineContext, Serializable
```

`left`가 또 `CombinedContext`일 수 있으므로, 요소가 셋이면 상자 안에 상자가 든 모양이 됩니다. `CoroutineName("작업") + Job() + Dispatchers.Default`는 이렇게 만들어집니다.

```text
CombinedContext(
    left    = CombinedContext(
                  left    = CoroutineName("작업"),
                  element = Job
              ),
    element = Dispatchers.Default
)
```

맨 바깥 상자의 `element`가 마지막에 더한 요소이고, 안으로 들어갈수록 먼저 더한 요소입니다. 소스 주석의 "left-biased list"는 이렇게 왼쪽으로 자라는 연결 리스트라는 뜻입니다. 오른쪽에 요소를 붙일 때는 기존 리스트를 `left`에 그대로 넣고 새 상자를 하나 씌우기만 하면 되므로, 기존 컨텍스트를 복사하지 않습니다. 컨텍스트가 불변이라서 이렇게 안쪽 상자를 여러 컨텍스트가 함께 써도 안전합니다.

세 연산은 이 구조를 따라 이렇게 구현됩니다.

```kotlin
// CoroutineContextImpl.kt (CombinedContext 의 일부)
override fun <E : Element> get(key: Key<E>): E? {
    var cur = this
    while (true) {
        cur.element[key]?.let { return it }   // 1. 바깥 상자의 요소부터 확인합니다
        val next = cur.left
        if (next is CombinedContext) {
            cur = next                         // 2. 없으면 안쪽 상자로 들어갑니다
        } else {
            return next[key]                   // 3. 맨 안쪽은 요소 하나입니다
        }
    }
}

public override fun <R> fold(initial: R, operation: (R, Element) -> R): R =
    operation(left.fold(initial, operation), element)

public override fun minusKey(key: Key<*>): CoroutineContext {
    element[key]?.let { return left }          // 1. 바깥 요소가 그 키면 안쪽만 돌려줍니다
    val newLeft = left.minusKey(key)           // 2. 아니면 안쪽에서 뺍니다
    return when {
        newLeft === left -> this               // 3. 안쪽에도 없었으면 자기 자신 그대로
        newLeft === EmptyCoroutineContext -> element  // 4. 안쪽이 비었으면 요소 하나만 남습니다
        else -> CombinedContext(newLeft, element)     // 5. 그 밖에는 바깥 요소를 다시 씌웁니다
    }
}
```

- `get`은 **바깥(마지막에 더한 요소)부터** 안쪽으로 찾아 들어갑니다.
- `fold`는 먼저 `left.fold`로 안쪽을 다 훑은 뒤 바깥 요소를 처리하므로, 요소를 **더한 순서대로(왼쪽부터)** 훑습니다. `toString()`도 `fold`로 만들어서 `[CoroutineName(작업), Job, Dispatchers.Default]`처럼 더한 순서로 찍힙니다.
- `minusKey`는 뺄 것이 없으면 새 객체를 만들지 않고 자기 자신을 돌려주고, 요소가 하나만 남으면 상자를 벗기고 요소 자체를 돌려줍니다.

실행해서 확인했습니다.

```kotlin
// OtherOps.kt
import kotlinx.coroutines.*
import kotlin.coroutines.ContinuationInterceptor
import kotlin.coroutines.CoroutineContext
import kotlin.coroutines.EmptyCoroutineContext

// 요소마다 짧은 이름을 붙여 앞에서부터 나열합니다
fun CoroutineContext.describe(): List<String> =
    fold(listOf()) { acc, element ->
        acc + when (element) {
            is CoroutineName -> "이름"
            is Job -> "Job"
            is CoroutineDispatcher -> "디스패처"
            else -> "기타"
        }
    }

fun main() {
    val context = CoroutineName("작업") + Job() + Dispatchers.Default
    println("0) ${context.describe()}")

    // 1. minusKey 는 그 키만 뺀 새 컨텍스트를 돌려줍니다. 원본은 그대로입니다
    val withoutName = context.minusKey(CoroutineName)
    println("1) 뺀 결과=${withoutName.describe()}, 원본=${context.describe()}")

    // 2. 없는 키를 빼면 같은 객체를 그대로 돌려줍니다
    val nameAndDispatcher = CoroutineName("작업") + Dispatchers.Default
    println("2) ${nameAndDispatcher.minusKey(Job) === nameAndDispatcher}")

    // 3. 하나만 남으면 CombinedContext 가 아니라 요소 자체가 됩니다
    val single = nameAndDispatcher.minusKey(ContinuationInterceptor)
    println("3) ${single::class.simpleName}")

    // 4. 다 빼면 EmptyCoroutineContext 가 됩니다
    println("4) ${single.minusKey(CoroutineName) === EmptyCoroutineContext}")

    // 5. 요소 순서가 달라도 같은 요소면 같은 컨텍스트입니다
    val name = CoroutineName("작업")
    val job = Job()
    println("5) ${(name + job) == (job + name)}")
}
```

```text
0) [이름, Job, 디스패처]
1) 뺀 결과=[Job, 디스패처], 원본=[이름, Job, 디스패처]
2) true
3) CoroutineName
4) true
5) true
```

5)처럼 `CombinedContext`의 `equals`는 요소 수가 같고 한쪽의 요소가 모두 다른 쪽에 들어 있는지만 봅니다. 더한 순서는 상관없습니다.

## plus의 동작 {#plus}

`plus`는 인터페이스에 기본 구현으로 들어 있습니다.

```kotlin
// CoroutineContext.kt
public operator fun plus(context: CoroutineContext): CoroutineContext =
    if (context === EmptyCoroutineContext) this else // fast path -- avoid lambda creation
        context.fold(this) { acc, element ->
            val removed = acc.minusKey(element.key)
            if (removed === EmptyCoroutineContext) element else {
                // make sure interceptor is always last in the context (and thus is fast to get when present)
                val interceptor = removed[ContinuationInterceptor]
                if (interceptor == null) CombinedContext(removed, element) else {
                    val left = removed.minusKey(ContinuationInterceptor)
                    if (left === EmptyCoroutineContext) CombinedContext(element, interceptor) else
                        CombinedContext(CombinedContext(left, element), interceptor)
                }
            }
        }
```

`left + right`를 하면 이렇게 진행됩니다.

1. **빈 컨텍스트를 더하면 그대로 돌려줍니다.** 람다 객체를 만드는 비용도 아끼려고 맨 앞에서 따로 처리합니다.
2. **오른쪽 컨텍스트를 `fold`로 훑습니다.** 누적값 `acc`는 왼쪽 컨텍스트에서 시작하고, 오른쪽의 요소를 하나씩 누적값에 붙여 나갑니다.
3. **같은 키를 먼저 뺍니다.** `acc.minusKey(element.key)`로 누적값에서 같은 키의 요소를 지웁니다. 같은 키가 양쪽에 있으면 오른쪽이 이기는 규칙이 이 한 줄에서 나옵니다.
4. **뺀 결과가 비었으면 요소 하나만 남깁니다.**
5. **아니면 요소를 붙이되, 인터셉터는 맨 끝으로 보냅니다.** 남은 컨텍스트에 인터셉터(디스패처)가 있으면 그것을 꺼내 두고, 나머지에 새 요소를 붙인 다음 인터셉터를 맨 바깥에 다시 씌웁니다. 인터셉터가 없으면 그냥 새 요소를 바깥에 씌웁니다.

5번의 이유는 주석에 적혀 있습니다. `get`은 바깥 상자부터 찾으므로, 인터셉터를 항상 맨 바깥에 두면 `context[ContinuationInterceptor]`가 첫 번째 확인에서 바로 끝납니다. 인터셉터는 코루틴을 시작하고 재개할 때마다 찾는 요소라 이 비용을 줄여 둔 것입니다.

`(JobA + DispatcherA) + (JobB + NameB)`를 따라가 보겠습니다.

1. 누적값은 왼쪽 `[JobA, DispatcherA]`에서 시작합니다. 오른쪽 `[JobB, NameB]`를 앞에서부터 하나씩 붙입니다.
2. **`JobB`를 붙입니다.** 누적값에서 `Job` 키를 빼면 `JobA`가 지워지고 `DispatcherA`만 남습니다. 남은 것에 인터셉터(`DispatcherA`)가 있으므로 꺼내 두고, 나머지는 비었으므로 `CombinedContext(JobB, DispatcherA)`, 즉 `[JobB, DispatcherA]`가 됩니다.
3. **`NameB`를 붙입니다.** `CoroutineName` 키는 누적값에 없으므로 빼도 그대로입니다. 인터셉터 `DispatcherA`를 꺼내 두면 `JobB`가 남고, 여기에 `NameB`를 붙인 뒤 인터셉터를 다시 씌워 `[JobB, NameB, DispatcherA]`가 됩니다.

`JobA`는 `JobB`로 바뀌었고, 디스패처는 더한 순서와 관계없이 맨 끝에 있습니다. 실행 결과도 같습니다.

```kotlin
// PlusTrace.kt
import kotlinx.coroutines.*
import kotlin.coroutines.CoroutineContext

val jobA = Job()
val jobB = Job()
val dispatcherA = Dispatchers.IO
val nameB = CoroutineName("B")

// 컨텍스트 안의 요소를 앞에서부터 이름으로 보여 줍니다
fun CoroutineContext.describe(): String {
    val labels = fold(listOf<String>()) { acc, element ->
        acc + when (element) {
            jobA -> "JobA"
            jobB -> "JobB"
            dispatcherA -> "DispatcherA"
            nameB -> "NameB"
            else -> element.toString()
        }
    }
    return labels.joinToString(prefix = "[", postfix = "]")
}

fun main() {
    val left = jobA + dispatcherA
    val right = jobB + nameB
    println("1) left  = ${left.describe()}")
    println("2) right = ${right.describe()}")

    // 같은 키(Job)는 오른쪽이 이기고, 디스패처는 맨 뒤로 갑니다
    val result = left + right
    println("3) left + right = ${result.describe()}")

    // 디스패처를 앞에 두고 더해도 결과에서는 맨 뒤입니다
    println("4) ${(dispatcherA + nameB).describe()}")
}
```

```text
1) left  = [JobA, DispatcherA]
2) right = [JobB, NameB]
3) left + right = [JobB, NameB, DispatcherA]
4) [NameB, DispatcherA]
```

책은 이 예제의 결과를 `((DispatcherA + JobB) + NameB)`로 설명하는데, 인터셉터를 맨 끝으로 보내는 규칙을 빼고 따라간 결과입니다. 어느 요소가 남는지는 같고 순서만 다릅니다.

## 요약 {#summary}

`CoroutineContext`는 `get`, `fold`, `plus`, `minusKey` 네 연산을 가진 표준 라이브러리 인터페이스입니다. 구현은 셋입니다. 요소 하나(`Element`)는 기본 구현 덕분에 그 자체로 컨텍스트가 되고, `EmptyCoroutineContext`는 빈 컨텍스트이며, 요소가 둘 이상이면 `CombinedContext`가 됩니다.

`CombinedContext`는 나머지 컨텍스트(`left`)와 요소 하나(`element`)를 묶은 상자를 겹친, 왼쪽으로 자라는 연결 리스트입니다. 새 요소를 붙일 때 기존 컨텍스트를 복사하지 않고 그 위에 상자를 하나 씌웁니다. `get`은 바깥(마지막에 더한 요소)부터 찾고, `fold`는 더한 순서대로 훑습니다.

`plus`는 오른쪽 컨텍스트를 `fold`로 훑으며 누적값에서 같은 키를 빼고(`minusKey`) 새 요소를 붙입니다. 같은 키는 오른쪽이 이기고, 인터셉터(디스패처)는 언제나 맨 바깥으로 옮겨서 `get` 한 번에 찾히게 합니다.
