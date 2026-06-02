# E8) 동시성과 Thread Safety

## 시작점: 공유 가변 상태 {#C0}

동시성 문제는 거의 항상 하나의 조건에서 시작합니다. **둘 이상의 스레드가 같은 가변 상태(mutable state)에 접근하고, 그중 적어도 하나가 쓰기**일 때입니다. 모든 스레드가 읽기만 한다면 문제는 생기지 않습니다.

**Thread Safety**란 여러 스레드가 동시에 같은 자원에 접근해도, 그 접근 순서와 무관하게 항상 올바른 결과를 보장하는 성질입니다. 이 토픽은 그 보장이 깨지는 세 가지 결함과 그것을 막는 도구를 다룹니다.

- **race condition**: 실행 순서에 따라 결과가 달라지는 결함.
- **메모리 가시성(memory visibility)**: 한 스레드의 쓰기가 다른 스레드에 보이는가의 문제.
- **deadlock**: 서로의 락을 기다리며 영원히 멈추는 상태.

가시성과 race condition은 별개의 문제이며, 둘 다 해결해야 코드가 안전해진다는 점이 이 토픽의 핵심입니다.

## Race Condition {#C1}

### 정의 {#race-condition-definition}

race condition이란 **둘 이상의 스레드가 공유 자원에 동시에 접근할 때, 그 실행 타이밍·순서에 따라 결과가 달라지는** 결함입니다. 가장 흔한 형태가 read-modify-write 연산입니다.

```kotlin
var count = 0

fun increment() {
    count++   // 한 줄처럼 보이지만 실제로는 세 단계다
}
```

`count++`는 원자적이지 않습니다. 바이트코드 수준에서 다음 세 단계로 나뉩니다.

1. `count`의 현재 값을 읽는다 (read).
2. 1을 더한다 (modify).
3. 결과를 다시 쓴다 (write).

### 왜 결과가 깨지는가 {#race-condition-interleaving}

두 스레드가 이 세 단계를 교차(interleaving) 실행하면 갱신이 사라집니다(lost update).

```kotlin
// count == 0 에서 시작, 두 스레드가 동시에 increment() 호출
// Thread A: read(0) ─────────────── +1 → write(1)
// Thread B:        read(0) → +1 → write(1)
// 기대값 2, 실제값 1 — 한 번의 증가가 사라졌다
```

이것이 race condition의 본질입니다. 코드는 "두 번 증가"를 의도했지만, 두 read가 같은 값 `0`을 읽었기 때문에 한 증가가 덮어써집니다. 단일 스레드에서는 절대 일어나지 않고, 재현이 비결정적이라 디버깅이 어렵습니다.

해결의 방향은 두 가지입니다. **연산을 원자적으로 만들거나(다음 절), 한 번에 한 스레드만 진입하도록 상호 배제하는 것**입니다.

## Mutex · synchronized · Atomic {#C2}

race condition을 막는 핵심 도구 세 가지입니다. 앞의 둘은 **상호 배제(mutual exclusion)**, 마지막은 **무락(lock-free) 원자 연산**으로 접근이 다릅니다.

### synchronized: JVM 모니터 락 {#synchronized-monitor-lock}

`synchronized`는 객체마다 하나씩 있는 **모니터 락(monitor lock)**을 사용합니다. 한 스레드가 락을 잡으면 다른 스레드는 그 락이 풀릴 때까지 블로킹됩니다. 따라서 임계 영역(critical section)에는 한 번에 한 스레드만 들어갑니다.

```kotlin
class Counter {
    private var count = 0

    @Synchronized              // 이 객체의 모니터 락으로 보호
    fun increment() {
        count++                // 한 번에 한 스레드만 read-modify-write
    }

    fun get(): Int = synchronized(this) { count }
}
```

주의할 점은, **읽기 쪽도 같은 락으로 보호해야** 한다는 것입니다. 위에서 `get()`도 `synchronized(this)`로 감싼 이유는 가시성 때문입니다. 락 획득·해제는 happens-before를 보장하므로(뒤의 메모리 가시성 절 참조), 보호되지 않은 읽기는 오래된 값을 볼 수 있습니다.

### Mutex: 코루틴용 일시 중단 락 {#mutex-suspending-lock}

`synchronized`는 스레드를 **블로킹**합니다. 코루틴에서는 스레드를 점유한 채 막으면 안 되므로, kotlinx.coroutines의 `Mutex`를 씁니다. `Mutex.lock()`은 블로킹 대신 코루틴을 **일시 중단(suspend)**시킵니다.

```kotlin
class Counter {
    private val mutex = Mutex()
    private var count = 0

    suspend fun increment() {
        mutex.withLock {       // 락 대기 동안 스레드를 막지 않고 suspend
            count++
        }
    }
}
```

`withLock`은 블록이 끝나거나 예외가 나도 락을 반드시 해제합니다. 중요한 제약 하나는 `Mutex`가 **재진입(reentrant)이 아니라는** 점입니다. 같은 코루틴이 이미 잡은 `Mutex`를 다시 `lock`하면 deadlock에 빠집니다. (`synchronized`는 재진입 가능합니다.)

### Atomic: CAS 기반 무락 연산 {#atomic-cas}

`AtomicInteger`, `AtomicReference` 등은 락 없이 원자성을 보장합니다. 핵심은 **CAS(Compare-And-Swap)**라는 CPU 명령어 수준의 원자 연산입니다.

```kotlin
val count = AtomicInteger(0)
count.incrementAndGet()        // 락 없이 원자적으로 +1
```

CAS는 "현재 값이 내가 읽은 값과 같으면 새 값으로 바꾸고, 다르면 실패"를 한 번의 원자 명령으로 수행합니다. `incrementAndGet`은 내부적으로 CAS가 성공할 때까지 재시도하는 루프입니다.

```kotlin
// incrementAndGet의 개념적 동작
var cur: Int
var next: Int
do {
    cur = count.get()                       // 현재 값 읽기
    next = cur + 1
} while (!count.compareAndSet(cur, next))   // 그 사이 값이 안 바뀌었으면 교체, 아니면 재시도
```

CAS는 락을 잡지 않으므로 락 경합이 적을 때 `synchronized`보다 빠르고, 블로킹이 없어 deadlock도 발생하지 않습니다. 반대로 경합이 심하면 `compareAndSet`이 계속 실패해 재시도 루프를 도는 비용 때문에 오히려 느려질 수 있습니다. 다만 단일 변수의 원자 연산에만 적합하며, **여러 변수를 함께 일관되게 갱신해야 한다면 락(또는 Mutex)이 필요**합니다.

### 셋의 선택 기준 {#choosing-primitive}

| 도구 | 방식 | 블로킹 | 적합한 상황 |
|------|------|--------|-------------|
| `synchronized` | 모니터 락 | 스레드 블로킹 | 일반 스레드, 여러 필드를 묶어 보호 |
| `Mutex` | 일시 중단 락 | suspend (논블로킹) | 코루틴 내부의 상호 배제 |
| `Atomic` | CAS 무락 | 없음 | 단일 변수의 원자 갱신 |

## 메모리 가시성 {#C3}

### 가시성은 원자성과 다른 문제다 {#visibility-vs-atomicity}

race condition을 막았다고 끝이 아닙니다. **한 스레드가 변수에 쓴 값이 다른 스레드에 언제 보이느냐**는 별개의 문제이며, 이것이 메모리 가시성입니다.

원인은 두 가지입니다.

1. **캐시**: 각 CPU 코어는 자신의 레지스터·캐시에 변수 사본을 둡니다. 한 코어의 쓰기가 메인 메모리로 플러시되고 다른 코어가 그것을 다시 읽기 전까지, 다른 코어는 **오래된 값(stale value)**을 봅니다.
2. **명령어 재정렬(reordering)**: 컴파일러와 CPU는 단일 스레드 의미가 보존되는 한 명령어 순서를 자유롭게 바꿉니다. 이 재정렬이 다른 스레드 입장에서는 예상치 못한 순서로 관측될 수 있습니다.

```kotlin
var running = true             // @Volatile 없음

// Thread A
fun stop() { running = false }

// Thread B — 이 루프가 영원히 안 끝날 수 있다
while (running) { /* ... */ }
```

위에서 Thread B는 `running`을 자신의 캐시에서만 읽어, A가 `false`로 바꿔도 그 변화를 영영 못 볼 수 있습니다. 이것은 race condition이 아니라 순수한 가시성 문제입니다.

### happens-before와 volatile {#volatile-happens-before}

Java 메모리 모델(JMM)은 **happens-before** 관계로 가시성을 정의합니다. "A가 B보다 happens-before면, A의 모든 쓰기가 B에서 보인다"는 보장입니다.

`@Volatile`은 이 관계를 만듭니다. volatile 변수에 대한 쓰기는 그 변수의 이후 읽기보다 happens-before이며, 다음을 보장합니다.

- 읽기는 항상 **최신 값**을 본다 (캐시가 아니라 메인 메모리에서).
- volatile 쓰기 **이전**의 모든 쓰기도 함께 보인다 (재정렬이 그 경계를 넘지 못함).

```kotlin
@Volatile var running = true   // 이제 Thread B는 변화를 즉시 본다
```

### volatile의 한계 {#volatile-limit}

`@Volatile`은 **가시성만** 해결하고 **원자성은 해결하지 못합니다.** read-modify-write는 volatile로도 안전하지 않습니다.

```kotlin
@Volatile var count = 0
fun increment() { count++ }    // 여전히 race condition — 읽기와 쓰기 사이가 갈라진다
```

`count++`는 읽기·수정·쓰기 세 단계이고, volatile은 각 단계의 가시성만 보장할 뿐 세 단계를 하나로 묶지 못합니다. 따라서 두 스레드의 교차로 갱신이 사라질 수 있습니다. **카운터처럼 복합 연산이면 `AtomicInteger`나 락을 써야** 합니다.

가시성을 만드는 다른 장치도 정리하면 다음과 같습니다.

- `synchronized` / `Mutex`: 락 해제 → 다음 획득 사이에 happens-before가 성립해, 락으로 보호된 모든 쓰기가 보입니다.
- `Atomic`: `get()`은 volatile 읽기 의미이고, CAS 연산 자체도 volatile 읽기·쓰기 의미를 포함합니다.

### 안드로이드 사례: Double-Checked Locking {#dcl-android}

`@Volatile`이 없으면 깨지는 대표 사례가 싱글톤의 DCL입니다.

```kotlin
class Repository private constructor() {
    companion object {
        @Volatile private var instance: Repository? = null

        fun getInstance(): Repository =
            instance ?: synchronized(this) {
                instance ?: Repository().also { instance = it }
            }
    }
}
```

`@Volatile`을 빼면, 객체 할당과 생성자 초기화의 재정렬 때문에 다른 스레드가 **아직 초기화가 끝나지 않은 객체**를 받을 수 있습니다. volatile이 그 재정렬을 막아 줍니다.

## Deadlock {#C4}

### 정의와 발생 조건 {#deadlock-conditions}

deadlock이란 **둘 이상의 스레드가 서로가 쥔 자원을 기다리며 영원히 멈추는** 상태입니다. 고전적으로 다음 네 조건이 동시에 성립할 때 발생합니다(Coffman 조건).

1. **상호 배제**: 자원을 한 번에 한 스레드만 쓸 수 있다.
2. **점유와 대기(hold and wait)**: 자원을 쥔 채로 다른 자원을 기다린다.
3. **비선점(no preemption)**: 쥔 자원을 강제로 뺏을 수 없다.
4. **순환 대기(circular wait)**: 스레드들이 원형으로 서로를 기다린다.

### 전형적 예시 {#deadlock-example}

두 스레드가 두 락을 **반대 순서로** 잡으면 순환 대기가 만들어집니다.

```kotlin
val lockA = Any()
val lockB = Any()

// Thread 1
synchronized(lockA) {
    synchronized(lockB) { /* ... */ }   // lockB를 기다림
}

// Thread 2
synchronized(lockB) {                   // Thread 2는 lockB를 이미 쥠
    synchronized(lockA) { /* ... */ }   // lockA를 기다림 → 서로 영원히 대기
}
```

Thread 1이 `lockA`를, Thread 2가 `lockB`를 잡은 순간, 둘은 각각 상대가 쥔 락을 기다리며 멈춥니다.

### 회피 전략 {#deadlock-prevention}

네 조건 중 하나만 깨면 deadlock을 막을 수 있습니다. 실무에서 쓰는 방법은 다음과 같습니다.

- **락 순서 고정(lock ordering)**: 모든 스레드가 항상 같은 순서로 락을 획득하면 순환 대기가 생기지 않습니다. 위 예시에서 두 스레드 모두 `lockA → lockB` 순서를 지키면 안전합니다.
- **타임아웃**: `ReentrantLock`의 `tryLock(timeout)`처럼 일정 시간 안에 못 잡으면 포기하고 잡은 락을 풀어, 점유와 대기를 깹니다.
- **락 범위 최소화**: 한 번에 하나의 락만 잡거나, 락을 잡은 채 외부 코드·콜백을 호출하지 않습니다.

코루틴에서도 같은 위험이 있습니다. 앞서 말했듯 `Mutex`는 재진입이 안 되므로, 이미 잡은 `Mutex`를 같은 코루틴이 다시 `withLock`하면 자기 자신을 기다리는 deadlock이 됩니다.

```kotlin
val mutex = Mutex()
suspend fun bad() = mutex.withLock {
    mutex.withLock { /* ... */ }   // 같은 Mutex 재진입 → 영원히 대기
}
```

## 요약 {#summary}

> **TL;DR** — 동시성 결함은 공유 가변 상태에서 시작합니다. 실행 순서에 따라 결과가 깨지는 race condition은 `synchronized`·`Mutex`의 상호 배제나 `Atomic`의 CAS로 막고, 한 스레드의 쓰기가 다른 스레드에 보이느냐는 메모리 가시성 문제는 `@Volatile`(happens-before)로 해결합니다. 가시성과 원자성은 별개라 volatile만으로는 카운터를 못 지킵니다. 락을 둘 이상 쓰면 순환 대기로 deadlock이 생길 수 있고, 락 순서를 고정해 막습니다.

1. **race condition**: read-modify-write가 스레드 교차로 갈라져 갱신이 사라지는 결함. 원자화하거나 상호 배제로 막는다.
2. **Mutex·synchronized·Atomic**: synchronized는 블로킹 모니터 락, Mutex는 코루틴용 일시 중단 락, Atomic은 CAS 기반 무락 단일 변수 연산.
3. **메모리 가시성**: 캐시·재정렬 때문에 쓰기가 안 보일 수 있다. `@Volatile`이 happens-before로 가시성을 보장하되, 원자성은 보장하지 못한다.
4. **deadlock**: 순환 대기로 서로의 락을 영원히 기다리는 상태. 락 순서 고정·타임아웃으로 막는다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) race condition이 정확히 무엇이고, count++ 같은 코드에서 왜 발생하나요?">

race condition은 둘 이상의 스레드가 공유 자원에 동시에 접근할 때 실행 순서·타이밍에 따라 결과가 달라지는 결함입니다. `count++`는 한 줄로 보이지만 실제로는 값을 읽고(read), 1을 더하고(modify), 다시 쓰는(write) 세 단계입니다.

두 스레드가 이 세 단계를 교차 실행하면, 둘 다 같은 값(예: 0)을 읽은 뒤 각각 1을 써서 결과가 2가 아니라 1이 됩니다. 한 증가가 덮어써져 사라지는 lost update입니다. 단일 스레드에서는 일어나지 않고 재현이 비결정적이라 디버깅이 어렵습니다. 막으려면 연산을 원자적으로 만들거나(`AtomicInteger`), 한 번에 한 스레드만 들어가도록 상호 배제(`synchronized`/`Mutex`)해야 합니다.

</def>
<def title="Q) synchronized, Mutex, Atomic은 각각 언제 쓰나요?">

`synchronized`는 JVM 모니터 락으로 임계 영역에 한 번에 한 스레드만 들이며, 락을 못 잡은 스레드는 블로킹됩니다. 일반 스레드 환경에서 여러 필드를 함께 묶어 보호할 때 적합합니다.

`Mutex`는 코루틴용입니다. `synchronized`처럼 스레드를 블로킹하는 대신, 락 대기 동안 코루틴을 일시 중단(suspend)시켜 스레드를 점유하지 않습니다. 코루틴 안에서 상호 배제가 필요할 때 씁니다. 단 재진입이 안 되므로 같은 코루틴이 같은 Mutex를 다시 잡으면 deadlock입니다.

`Atomic`(AtomicInteger 등)은 CAS(Compare-And-Swap)라는 CPU 원자 명령으로 락 없이 원자성을 보장합니다. 락 경합이 적을 때 빠르고 deadlock이 없지만, 단일 변수의 원자 연산에만 적합하고 여러 변수를 일관되게 갱신하려면 락이 필요합니다.

</def>
<def title="Q) @Volatile은 무엇을 보장하나요? volatile만으로 카운터를 안전하게 만들 수 있나요?">

`@Volatile`은 메모리 가시성을 보장합니다. 각 CPU 코어가 캐시에 변수 사본을 두기 때문에 한 스레드의 쓰기가 다른 스레드에 안 보일 수 있는데, volatile은 읽기가 항상 메인 메모리의 최신 값을 보도록 하고, JMM의 happens-before 관계를 만들어 명령어 재정렬이 그 경계를 넘지 못하게 합니다.

하지만 volatile은 가시성만 해결하고 원자성은 해결하지 못합니다. `count++`는 읽기·수정·쓰기 세 단계인데, volatile은 각 단계의 가시성만 보장할 뿐 세 단계를 하나로 묶지 못합니다. 따라서 두 스레드의 교차로 여전히 race condition이 발생합니다. 카운터처럼 복합 연산이면 `AtomicInteger`나 락을 써야 합니다. volatile은 단순 플래그(예: `running = false`)나 DCL 싱글톤처럼 가시성·재정렬만 문제인 경우에 적합합니다.

</def>
<def title="Q) 메모리 가시성 문제와 race condition은 같은 문제인가요?">

다른 문제입니다. race condition은 여러 스레드의 연산이 교차해 결과가 깨지는 원자성 문제이고, 메모리 가시성은 한 스레드가 쓴 값이 다른 스레드에 언제 보이느냐의 문제입니다.

가시성 문제는 CPU 코어별 캐시와 명령어 재정렬에서 비롯됩니다. 예를 들어 `while (running)` 루프는 다른 스레드가 `running = false`로 바꿔도 그 변화를 캐시 때문에 영영 못 보고 무한 루프에 빠질 수 있는데, 이는 교차 실행이 없어도 발생하므로 race condition이 아닙니다. 두 문제는 독립적이라 둘 다 해결해야 합니다. `synchronized`나 `Mutex`는 락의 happens-before로 두 문제를 동시에 해결하고, `@Volatile`은 가시성만, `Atomic`은 둘 다 해결합니다.

</def>
<def title="Q) deadlock은 어떤 조건에서 생기고, 어떻게 막나요?">

deadlock은 둘 이상의 스레드가 서로가 쥔 자원을 기다리며 영원히 멈추는 상태입니다. 상호 배제, 점유와 대기, 비선점, 순환 대기라는 네 조건(Coffman 조건)이 동시에 성립할 때 발생합니다. 전형적으로 두 스레드가 두 락을 반대 순서로 잡을 때, 각자 하나씩 쥔 채 상대의 락을 기다리며 순환 대기가 만들어집니다.

네 조건 중 하나만 깨면 막을 수 있습니다. 가장 실용적인 방법은 락 순서 고정으로, 모든 스레드가 항상 같은 순서(예: lockA → lockB)로 락을 잡으면 순환 대기가 생기지 않습니다. 그 외에 `tryLock(timeout)`으로 일정 시간 안에 못 잡으면 포기해 점유와 대기를 깨거나, 락 범위를 최소화하고 락을 쥔 채 외부 콜백을 호출하지 않는 방법이 있습니다. 코루틴에서는 재진입 불가인 Mutex를 같은 코루틴이 중첩해서 잡는 경우도 deadlock이 됩니다.

</def>
</deflist>
