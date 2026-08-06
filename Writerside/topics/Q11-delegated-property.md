# Q11) 위임 프로퍼티(delegated property)란 무엇인가

위임 프로퍼티는 프로퍼티의 **getter와 setter 로직을 다른 객체에 맡기는** 기능입니다. `by` 키워드로 프로퍼티와 delegate 객체를 연결하면, 프로퍼티에 접근할 때마다 그 객체가 대신 처리합니다.

```kotlin
val lazyValue: String by lazy {
    println("Computed!")
    "Hello, Kotlin!"
}

println(lazyValue)   // Computed! / Hello, Kotlin!
println(lazyValue)   // Hello, Kotlin!  — 초기화 람다는 다시 실행되지 않는다
```

"값을 언제 계산할지", "값이 바뀌면 무엇을 할지" 같은 **프로퍼티 관리 로직을 비즈니스 로직에서 분리**하는 것이 목적입니다.

> 이 문서는 위임이 **내부적으로 어떻게 동작하는지**에 집중합니다. 커스텀 delegate 작성법과 클래스 위임(`class A : B by b`)을 포함한 전반적인 사용법은 [E3) Kotlin Delegation](E3-Kotlin-Delegation.md)에서 다룹니다.

## 동작 원리 {#how-it-works}

`by` 뒤에 오는 객체가 delegate입니다. 컴파일러는 이 객체에게 다음 연산자 함수를 요구합니다.

```kotlin
import kotlin.reflect.KProperty

class Delegate {
    operator fun getValue(thisRef: Any?, property: KProperty<*>): String = property.name
    operator fun setValue(thisRef: Any?, property: KProperty<*>, value: String) { /* ... */ }
}

class Owner {
    var custom: String by Delegate()
}
```

- `thisRef` — 프로퍼티를 소유한 객체. 최상위 프로퍼티면 `null`입니다.
- `property` — 프로퍼티의 메타데이터. 이름·타입 등을 담습니다.

`val`이면 `getValue`만, `var`면 `setValue`까지 필요합니다. 인터페이스를 구현하지 않아도 되고, **연산자 시그니처만 맞으면** 됩니다. 표준 라이브러리는 `ReadOnlyProperty`/`ReadWriteProperty` 인터페이스도 제공합니다.

## 표준 위임 {#standard-delegates}

Kotlin이 기본 제공하는 네 가지입니다.

| delegate | 용도 |
|---|---|
| `lazy {}` | 첫 접근 시점에 한 번만 초기화하고 이후 캐시 |
| `Delegates.observable()` | 값이 바뀔 때마다 콜백 |
| `Delegates.vetoable()` | 조건을 만족할 때만 변경 수락 |
| `by map` | 프로퍼티 값을 `Map`에서 조회 |

```kotlin
import kotlin.properties.Delegates

var observableValue: String by Delegates.observable("Initial") { _, old, new ->
    println("Value changed from $old to $new")
}

var vetoableValue: Int by Delegates.vetoable(0) { _, old, new ->
    new > old      // 증가할 때만 수락
}

class User(val map: Map<String, Any?>) {
    val name: String by map
    val age: Int by map
}
```

각 delegate의 상세한 사용 예제는 [E3) Kotlin Delegation](E3-Kotlin-Delegation.md)에 정리되어 있습니다.

## Pro Tips {#pro-tips}

### lazy의 내부 구조 {#lazy-internals}

`by lazy`는 문법이 단순하지만 안쪽은 스레드 안전성 요구에 따라 구현이 나뉘어 있습니다. 출발점은 인터페이스 하나입니다.

```kotlin
public interface Lazy<out T> {
    public val value: T
    public fun isInitialized(): Boolean
}
```

`value`가 진입점입니다. 처음 접근하면 초기화 람다를 실행하고, 이후에는 캐시된 값을 돌려줍니다. `isInitialized()`는 초기화를 유발하지 않고 상태만 확인합니다.

프로퍼티 위임이 성립하는 이유는 `Lazy`에 붙은 확장 연산자 때문입니다.

```kotlin
@kotlin.internal.InlineOnly
public inline operator fun <T> Lazy<T>.getValue(thisRef: Any?, property: KProperty<*>): T = value
```

프로퍼티 읽기가 곧 `lazy.value` 읽기로 바뀝니다.

모든 구현은 **`UNINITIALIZED_VALUE`라는 싱글톤 마커**로 상태를 추적합니다. `_value` 필드를 이 마커로 초기화해 두고, 접근 시 아직 마커와 동일한지 검사합니다. 초기화가 끝나면 두 가지가 일어납니다.

1. `_value`가 계산 결과로 교체됩니다.
2. **초기화 람다 참조가 `null`로 지워집니다.** 람다가 캡처한 객체들이 GC 대상이 되어 누수를 막습니다.

`lazy()`는 요청한 모드에 따라 세 구현 중 하나를 돌려주는 팩토리입니다.

| 모드 | 구현체 | 메커니즘 | 특징 |
|---|---|---|---|
| `SYNCHRONIZED`(기본) | `SynchronizedLazyImpl` | 이중 검사 잠금 | 초기화 **정확히 한 번** 보장 |
| `PUBLICATION` | `SafePublicationLazyImpl` | CAS(잠금 없음) | 람다가 **여러 번 실행될 수 있음**, 최종 값은 하나 |
| `NONE` | `UnsafeLazyImpl` | 검사만, 동기화 없음 | 가장 빠름, **스레드 안전성 없음** |

기본값인 `SynchronizedLazyImpl`은 전형적인 이중 검사 잠금 패턴입니다.

```kotlin
// 명확성을 위해 단순화
override val value: T
    get() {
        if (_value !== UNINITIALIZED_VALUE) {
            return _value as T          // 1차 검사: 잠금 없이 빠르게 반환
        }
        return synchronized(lock) {
            if (_value !== UNINITIALIZED_VALUE) {
                _value as T             // 2차 검사: 잠금 대기 중 다른 스레드가 끝냈을 수 있다
            } else {
                val typedValue = initializer!!()
                _value = typedValue
                initializer = null
                typedValue
            }
        }
    }
```

두 번째 검사가 핵심입니다. 첫 검사와 잠금 획득 사이에 다른 스레드가 초기화를 끝냈을 수 있는 경쟁 조건을 처리합니다. `_value`의 `volatile` 표시와 `synchronized`의 메모리 보장이 결합되어 모든 스레드에 결과가 보입니다.

`SafePublicationLazyImpl`은 잠금 대신 `AtomicReferenceFieldUpdater`의 `compareAndSet`을 씁니다. 여러 스레드가 동시에 람다를 실행할 수 있고, CAS 경쟁에서 이긴 하나의 값만 최종 게시됩니다. 나머지는 자기 계산 결과를 버립니다. **초기화가 싸고 멱등할 때** 잠금 경합을 피하는 선택지입니다.

> **선택 기준** — 단일 스레드에서만 접근한다고 확신할 수 있으면 `NONE`이 가장 빠릅니다. Android에서 메인 스레드에서만 쓰는 뷰 참조 같은 경우가 여기 해당합니다. 확신이 없으면 기본값을 그대로 둡니다.

### 바이트코드는 delegate마다 다르다 {#bytecode}

`by`가 붙은 프로퍼티는 값을 담는 필드 대신 **delegate 객체를 담는 `$delegate` 필드**로 컴파일됩니다. 그런데 그 뒤 모습이 delegate 종류에 따라 갈립니다.

먼저 커스텀 delegate입니다.

```kotlin
class Owner {
    val custom: String by Delegate()
}
```

```java
public final class Owner {
  static final kotlin.reflect.KProperty<java.lang.Object>[] $$delegatedProperties;
  private final Delegate custom$delegate;
  public final java.lang.String getCustom();
}
```

getter는 이렇게 호출합니다.

```java
custom$delegate.getValue(this, $$delegatedProperties[0])
```

`$$delegatedProperties`는 프로퍼티 메타데이터(`KProperty`)를 담은 static 배열입니다. `getValue`의 두 번째 인자로 넘겨야 하므로 생성됩니다.

이제 `lazy`를 보면 다릅니다.

```kotlin
class UserSession {
    val heavyUserData: String by lazy { "User Profile Data" }
}
```

```java
public final class UserSession {
  private final kotlin.Lazy heavyUserData$delegate;
  public final java.lang.String getHeavyUserData();
  private static final java.lang.String heavyUserData_delegate$lambda$0();
}
```

**`$$delegatedProperties` 배열이 없습니다.** getter도 인자 없이 부릅니다.

```java
invokeinterface kotlin/Lazy.getValue:()Ljava/lang/Object;
```

`Lazy<T>.getValue` 확장이 `@InlineOnly inline`이고 본문이 `= value`뿐이기 때문입니다. 인라인되면서 사용되지 않는 `property` 인자가 통째로 사라지고, 결국 `lazy.value` 한 번 읽는 코드만 남습니다. 즉 `KProperty` 메타데이터를 만들 이유가 없어집니다.

여기서 얻을 수 있는 결론은 두 가지입니다.

- **`by lazy`의 런타임 비용은 생각보다 작습니다.** 리플렉션 객체를 만들지 않고, 초기화 이후에는 필드 검사 한 번 + `value` 반환이 전부입니다.
- **커스텀 delegate는 `KProperty` 객체를 프로퍼티마다 하나씩 만듭니다.** 클래스당 static 배열 하나에 담기므로 인스턴스마다 늘지는 않지만, 리플렉션 메타데이터가 생긴다는 점은 알아 둘 필요가 있습니다.

> 이 결과는 Kotlin 2.2.20으로 컴파일해 `javap`으로 확인한 것입니다. 오래된 자료에서는 `lazy`에도 `$$delegatedProperties`가 생성되는 디컴파일 결과를 볼 수 있는데, 현재 컴파일러는 그렇게 만들지 않습니다.

### 로컬 위임 프로퍼티 {#local}

위임은 클래스 프로퍼티뿐 아니라 **함수 안의 지역 변수**에도 쓸 수 있습니다.

```kotlin
import kotlin.reflect.KProperty

class Delegate {
    operator fun getValue(t: Any?, p: KProperty<*>): Int = 1
}

fun box(): String {
    val prop: Int by Delegate()
    return if (prop == 1) "OK" else "fail"
}
```

지역 변수에도 같은 위임 로직을 재사용할 수 있어, 함수 안에서만 필요한 지연 계산을 표현할 때 유용합니다. 함수 안에서 무거운 값을 조건부로만 쓰는 경우 `val config by lazy { loadConfig() }`처럼 두면 해당 분기에 들어갈 때만 계산됩니다.

### 위임의 비용 {#cost}

편의에는 대가가 따릅니다. 위임 프로퍼티 하나마다

- **객체가 하나 더 생깁니다.** `by lazy`는 `SynchronizedLazyImpl` 인스턴스를, 커스텀 delegate는 해당 delegate 인스턴스를 각각 보유합니다.
- **간접 호출이 한 단계 늘어납니다.** 필드를 직접 읽는 대신 delegate의 `getValue`를 거칩니다.

대부분의 상황에서 무시할 만한 수준이지만, **리스트 항목처럼 수천 개씩 만들어지는 객체**에 `by lazy`를 여러 개 달면 인스턴스 수가 그만큼 배로 늘어납니다. 이런 자리에서는 일반 프로퍼티나 커스텀 getter가 적절합니다.

## 요약 {#summary}

> **TL;DR** — 위임 프로퍼티는 `by` 키워드로 getter/setter를 다른 객체에 맡기는 기능이며, delegate는 `getValue`/`setValue` 연산자 시그니처만 맞추면 됩니다. `lazy`는 `UNINITIALIZED_VALUE` 마커로 상태를 추적하고 스레드 안전성 모드에 따라 세 가지 구현 중 하나를 사용하며, 기본값은 이중 검사 잠금을 쓰는 `SynchronizedLazyImpl`입니다. 바이트코드에서는 `$delegate` 필드가 생기고, 커스텀 delegate는 `$$delegatedProperties` 메타데이터 배열까지 만들어지지만 `lazy`는 인라인되어 그 배열 없이 컴파일됩니다.

1. **정체**: `by` 키워드로 프로퍼티 접근 로직을 delegate 객체에 위임하는 기능.
2. **규약**: `getValue(thisRef, property)`와(`var`면) `setValue(thisRef, property, value)` 연산자만 있으면 됨. 인터페이스 구현은 선택.
3. **표준 delegate**: `lazy`(지연 초기화), `observable`(변경 감지), `vetoable`(변경 거부), `by map`(맵 조회).
4. **lazy 내부**: `UNINITIALIZED_VALUE` 마커로 상태 추적. 초기화 후 람다 참조를 `null`로 지워 누수 방지.
5. **스레드 안전성 모드**: `SYNCHRONIZED`(기본, 이중 검사 잠금) / `PUBLICATION`(CAS, 람다 중복 실행 가능) / `NONE`(동기화 없음, 가장 빠름).
6. **바이트코드**: 값 대신 `$delegate` 필드를 보유. 커스텀 delegate는 `$$delegatedProperties` 배열 생성, `lazy`는 `@InlineOnly`라 배열 없이 `Lazy.getValue()` 직접 호출.
7. **비용**: 프로퍼티마다 delegate 객체 하나 + 간접 호출 한 단계. 대량 생성되는 객체에서는 주의.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 위임 프로퍼티란 무엇인가요?">

`by` 키워드를 사용해 프로퍼티의 getter와 setter 로직을 다른 객체(delegate)에 맡기는 기능입니다. 프로퍼티에 접근하면 컴파일러가 delegate의 `getValue`를, 값을 대입하면 `setValue`를 호출하도록 코드를 생성합니다. 지연 초기화, 변경 관찰, 변경 거부, 맵 기반 조회처럼 반복적으로 등장하는 프로퍼티 관리 패턴을 비즈니스 로직에서 분리할 수 있어 코드가 간결해지고 재사용성이 높아집니다.

</def>
<def title="Q) delegate 객체가 갖춰야 할 조건은 무엇인가요?">

특정 인터페이스를 구현할 필요는 없고 연산자 함수의 시그니처만 맞으면 됩니다. 읽기 전용(`val`) 프로퍼티라면 `operator fun getValue(thisRef: Any?, property: KProperty<*>): T`가, 가변(`var`) 프로퍼티라면 여기에 `operator fun setValue(thisRef: Any?, property: KProperty<*>, value: T)`가 추가로 필요합니다. `thisRef`는 프로퍼티를 소유한 객체이고(최상위 프로퍼티면 `null`), `property`는 이름과 타입 등 프로퍼티 메타데이터를 담습니다. 표준 라이브러리의 `ReadOnlyProperty`와 `ReadWriteProperty` 인터페이스를 구현하는 방법도 있습니다.

</def>
<def title="Q) lazy의 내부 메커니즘을 설명해 주세요.">

`Lazy<T>` 인터페이스가 `value` 프로퍼티와 `isInitialized()` 함수를 정의하고, `Lazy<T>.getValue` 확장 연산자가 프로퍼티 읽기를 `value` 읽기로 연결합니다. 구현체는 `UNINITIALIZED_VALUE`라는 싱글톤 마커로 초기화 여부를 추적하는데, `_value`가 아직 이 마커와 같으면 초기화 람다를 실행하고 결과로 교체합니다. 이때 초기화 람다 참조를 `null`로 지워 람다가 캡처한 객체들이 GC될 수 있도록 합니다. `lazy()` 함수는 스레드 안전성 모드에 따라 `SynchronizedLazyImpl`, `SafePublicationLazyImpl`, `UnsafeLazyImpl` 중 하나를 반환하는 팩토리입니다.

</def>
<def title="Q) LazyThreadSafetyMode의 세 가지 모드는 어떻게 다른가요?">

`SYNCHRONIZED`가 기본값이며 `SynchronizedLazyImpl`을 사용합니다. 이중 검사 잠금 패턴으로 잠금 밖에서 한 번, 잠금 안에서 한 번 검사해 초기화가 정확히 한 번만 실행되도록 보장하면서도 두 번째 이후 접근은 잠금 없이 빠르게 처리합니다. `PUBLICATION`은 `SafePublicationLazyImpl`로 `compareAndSet`을 사용하는 잠금 없는 방식이라 여러 스레드가 초기화 람다를 중복 실행할 수 있지만 최종적으로 게시되는 값은 하나입니다. 초기화가 저렴하고 멱등할 때 적합합니다. `NONE`은 `UnsafeLazyImpl`로 동기화가 전혀 없어 가장 빠르지만, 단일 스레드에서만 초기화되고 접근된다고 확신할 수 있을 때만 사용해야 합니다.

</def>
<def title="Q) 위임 프로퍼티는 바이트코드로 어떻게 컴파일되나요?">

프로퍼티 값을 담는 필드 대신 delegate 객체를 담는 `프로퍼티명$delegate` 필드가 생성되고, getter는 그 delegate의 `getValue`에 호출을 위임합니다. 커스텀 delegate의 경우 `getValue`가 `KProperty` 인자를 받으므로 프로퍼티 메타데이터를 담은 static 배열 `$$delegatedProperties`도 함께 생성되어 `delegate.getValue(this, $$delegatedProperties[0])` 형태로 호출됩니다. 반면 `by lazy`는 `Lazy<T>.getValue` 확장이 `@InlineOnly inline`이고 본문이 `= value`뿐이라 인라인되면서 사용하지 않는 `property` 인자가 사라집니다. 그 결과 `$$delegatedProperties` 배열 없이 `Lazy.getValue()`를 직접 호출하는 코드만 남습니다.

</def>
<def title="Q) 위임 프로퍼티를 남용하면 어떤 문제가 있나요?">

프로퍼티마다 delegate 객체가 하나씩 추가로 생성되고 프로퍼티 접근이 간접 호출 한 단계를 더 거칩니다. `by lazy`라면 `SynchronizedLazyImpl` 인스턴스가, 커스텀 delegate라면 해당 delegate 인스턴스가 소유 객체마다 만들어집니다. 대부분의 경우 무시할 수 있는 비용이지만, 리스트 항목처럼 수천 개씩 생성되는 객체에 위임 프로퍼티를 여러 개 두면 인스턴스 수가 배로 늘어납니다. 이런 자리에서는 일반 프로퍼티나 저장 공간을 만들지 않는 커스텀 getter를 쓰는 편이 낫습니다.

</def>
</deflist>
