# Q12) lazy 위임과 lateinit의 차이

둘 다 "선언 시점에 값을 정하지 않는다"는 목적은 같지만, **누가 초기화를 책임지는가**가 다릅니다.

- `by lazy` — **컴파일러가** 첫 접근 시점에 알아서 초기화합니다. 개발자는 계산식만 넘깁니다.
- `lateinit` — **개발자가** 어딘가에서 값을 넣어줘야 합니다. 안 넣고 읽으면 예외가 납니다.

```kotlin
val lazyValue: String by lazy {
    println("Computed once")
    "Hello, Lazy"
}

lateinit var message: String
fun setup() { message = "Hello, Lateinit" }
```

이 차이에서 나머지 제약이 전부 따라 나옵니다.

## 한눈에 비교 {#comparison}

| | `by lazy` | `lateinit` |
|---|---|---|
| 선언 | `val`만 | `var`만 |
| 초기화 주체 | 컴파일러(첫 접근 시) | 개발자(명시적 대입) |
| 재할당 | 불가 | 가능 |
| 스레드 안전 | 기본 보장 | 보장 없음 |
| 초기화 전 접근 | 발생하지 않음 | `UninitializedPropertyAccessException` |
| primitive 타입 | 가능 | **불가** |
| nullable 타입 | 가능 | **불가** |
| 초기화 여부 확인 | 필요 없음 | `::prop.isInitialized` |

## lateinit의 제약 세 가지 {#lateinit-limits}

`lateinit`은 붙일 수 있는 자리가 좁습니다. 컴파일러가 정확히 알려 줍니다.

```kotlin
class A {
    lateinit val a: String     // ①
    lateinit var b: Int        // ②
    lateinit var c: String?    // ③
}
```

```
① error: 'lateinit' modifier is allowed only on mutable properties.
② error: 'lateinit' modifier is not allowed on properties of primitive types.
③ error: 'lateinit' modifier is not allowed on properties of a type with nullable upper bound.
```

이유는 하나로 이어집니다. `lateinit`은 **"아직 값이 없음"을 내부적으로 `null`로 표시**합니다.

- `val`은 나중에 대입할 수 없으니 애초에 성립하지 않습니다.
- `Int` 같은 primitive는 백킹 필드가 JVM 원시 타입(`int`)이라 표시로 쓸 `null` 자리가 없습니다.
- 타입이 이미 nullable이면 `null`이 "미초기화"인지 "값이 null"인지 구분되지 않습니다.

primitive 항목은 오해하기 쉬운 지점입니다. "`Int`는 `null`을 못 담아서"라고만 하면, non-null인 `String`도 마찬가지 아니냐는 반문이 바로 나옵니다. 실제로 코틀린 타입 레벨에서는 둘 다 `null`을 담을 수 없습니다.

**차이는 코틀린 타입이 아니라 백킹 필드의 JVM 표현에 있습니다.**

```kotlin
class Holder {
    lateinit var s: String
    var plainInt: Int = 0
}
```

```
public java.lang.String s;      // 참조 필드
private int plainInt;           // JVM 원시 필드
```

코틀린의 non-null은 **컴파일 타임 약속**일 뿐이고, `String` 백킹 필드는 평범한 참조라 물리적으로는 `null`에서 시작합니다. `lateinit`은 정확히 그 틈을 이용합니다 — 필드를 `null`인 채로 두고, 읽는 지점마다 검사를 끼워 넣어 약속을 유지합니다.

반면 `Int`는 JVM `int`로 컴파일되어 `0`에서 시작하고, `0`은 멀쩡한 정상값입니다. 미초기화를 표시할 여분의 상태가 **값 공간에 존재하지 않습니다.** 그래서 금지됩니다.

> **primitive를 지연 초기화하고 싶다면** — `by lazy`를 쓰거나, `var count: Int? = null`로 두고 직접 검사하거나, `0` 같은 기본값으로 시작하면 됩니다. `lateinit`만 안 되는 것이지 방법이 없는 것은 아닙니다.

## 초기화 여부 확인 {#is-initialized}

`lateinit` 프로퍼티는 접근 전에 초기화 여부를 물어볼 수 있습니다.

```kotlin
class Service {
    private lateinit var config: Configuration

    fun ready(): Boolean = ::config.isInitialized
}
```

`isInitialized`는 **`lateinit` 프로퍼티에만** 쓸 수 있습니다. 일반 프로퍼티에는 없습니다.

컴파일 결과는 단순합니다. 사실상 `null` 검사입니다.

```java
public final boolean ready();
  getfield config
  ifnull  → false
  → true
```

## Pro Tips {#pro-tips}

### 가시성에 따른 lateinit 바이트코드 {#bytecode}

`lateinit var`는 바이트코드에서 **평범한 nullable 필드**가 됩니다. 필드 자체는 `null`을 막지 않습니다. 약속을 강제하는 것은 **읽는 쪽에 삽입되는 검사**입니다.

그런데 그 검사가 어디에 들어가는지는 가시성에 따라 갈립니다.

**public일 때 — getter 안에 들어갑니다.**

```kotlin
class Svc { lateinit var config: String }
```

```java
public final class Svc {
  public java.lang.String config;          // 필드는 그냥 nullable
  public final java.lang.String getConfig();   // 여기에 검사
  public final void setConfig(java.lang.String);
}
```

```java
public final java.lang.String getConfig();
  getfield config
  ifnull → Intrinsics.throwUninitializedPropertyAccessException("config")
  areturn
```

**private일 때 — getter 자체가 생성되지 않고, 사용하는 자리마다 검사가 인라인됩니다.**

```kotlin
class Service {
    private lateinit var config: Configuration
    fun doWork() = config.settings
}
```

```java
public final class Service {
  private Configuration config;            // getter/setter 없음
  public final java.lang.String doWork();
}
```

```java
public final java.lang.String doWork();
  getfield config
  ifnonnull → 계속
  else → Intrinsics.throwUninitializedPropertyAccessException("config")
  invokevirtual Configuration.getSettings()
```

Q10에서 본 것과 같은 원리입니다. `private`은 외부에 노출할 일이 없으니 접근자를 만들지 않고, 컴파일러가 사용 지점에서 직접 처리합니다.

> **예외 이름이 중요한 이유** — 검사가 없었다면 `config.settings`에서 그냥 `NullPointerException`이 났을 것입니다. `UninitializedPropertyAccessException`은 **어떤 프로퍼티가 초기화되지 않았는지**를 이름으로 알려 줍니다. 실패를 빠르고 명확하게 만드는 장치입니다.

### lazy가 val 전용인 이유 {#lazy-val-only}

"`lazy`는 `val` 전용"이라고 외우기 쉬운데, 실제로는 **위임 규약을 만족하지 못해서** 생기는 결과입니다.

```kotlin
class B { var x: String by lazy { "a" } }
```

```
error: type 'Lazy<String>' has no method 'setValue(B, KMutableProperty1<*, *>, String)',
       so it cannot serve as a delegate for var (read-write property).
```

Q11에서 본 대로 `var` 프로퍼티를 위임하려면 delegate에 `setValue` 연산자가 있어야 합니다. `Lazy` 인터페이스에는 `value`와 `isInitialized()`뿐이라 `setValue`가 없습니다. 그래서 `var`에 붙일 수 없는 것입니다.

직접 만든 delegate에 `setValue`를 넣으면 `var`에도 얼마든지 붙습니다. 제약은 `by`가 아니라 `Lazy`에 있습니다.

### 로컬·최상위 lateinit {#local-lateinit}

`lateinit`은 클래스 프로퍼티뿐 아니라 **함수 안의 지역 변수와 파일 최상위 프로퍼티에도** 쓸 수 있습니다. [KEEP 제안서](https://github.com/Kotlin/KEEP/blob/master/proposals/local-and-top-level-lateinit-vars.md)로 논의되던 내용이 **Kotlin 1.2에 반영**되었습니다.

```kotlin
lateinit var topLevel: String   // 최상위 프로퍼티

fun foo() {
    lateinit var x: Bar         // 지역 변수
    synchronized(lock) { x = bar() }
    // ...
}
```

미초기화 상태로 읽으면 클래스 프로퍼티와 똑같이 `UninitializedPropertyAccessException`이 납니다.

### 지역 변수의 null 준비 주체 {#local-aconst-null}

여기서 한 가지 의문이 생깁니다. 앞에서 `lateinit`은 미초기화를 `null`로 표시한다고 했는데, **JVM은 지역 변수에 기본값을 주지 않습니다.** 필드와 배열 원소만 자동으로 0/`null`로 채워지고, 지역 변수는 사용 전에 반드시 대입돼 있어야 하며 검증기가 이를 강제합니다.

그럼 지역 `lateinit`은 무엇을 검사하는 걸까요. 바이트코드를 보면 답이 나옵니다.

```
0: aconst_null      // 컴파일러가 null을 직접 밀어 넣는다
1: astore_0
2: invokestatic  bar()
5: astore_0         // 실제 대입
6: aload_0
7: dup
8: ifnonnull     18
11: pop
12: ldc           "x"
14: invokestatic  Intrinsics.throwUninitializedPropertyAccessException
18: ...
```

첫 두 명령이 핵심입니다. JVM이 `null`을 주지 않으니 **컴파일러가 슬롯 맨 앞에 `aconst_null`을 손수 깔아 둡니다.** 그 뒤는 [앞에서 본 필드 케이스](#bytecode)와 동일하게 `ifnonnull` 검사입니다. `null`을 표시로 쓰고 읽는 지점에서 검사한다는 뼈대는 어디서든 같습니다.

정리하면 세 경우의 메커니즘은 같고, `null`을 누가 준비하느냐만 다릅니다.

| 대상 | 미초기화 표시용 `null` |
|---|---|
| 필드 | JVM이 자동으로 채움 (참조 필드 기본값) |
| 지역 변수 | 컴파일러가 `aconst_null`로 직접 깔아 줌 |
| primitive | 깔아 줄 `null` 자체가 없음 → 금지 |

### 지역 변수의 isInitialized 제약 {#local-isinitialized}

남아 있는 제약이 하나 있습니다. `::prop.isInitialized`는 **클래스 프로퍼티에만** 쓸 수 있고 지역 변수에는 쓸 수 없습니다.

```kotlin
fun foo() {
    lateinit var x: Bar
    println(::x.isInitialized)   // error
}
```

```
error: references to variables aren't supported yet
```

지역 변수에 대한 참조(`::x`) 자체가 아직 지원되지 않기 때문입니다. 지역에서 초기화 여부를 확인해야 한다면 `lateinit` 대신 nullable로 선언하고 직접 검사해야 합니다.

### Android에서의 선택 기준 {#android}

판단 기준은 **값을 누가 언제 주느냐**입니다.

**`lateinit`이 맞는 경우** — 프레임워크나 DI가 나중에 값을 넣어 줄 때.

```kotlin
class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding   // onCreate에서 대입

    @Inject lateinit var repository: UserRepository     // Hilt가 주입
}
```

**`by lazy`가 맞는 경우** — 값을 스스로 계산할 수 있고, 비용이 있거나 안 쓰일 수도 있을 때.

```kotlin
class DetailActivity : AppCompatActivity() {
    private val itemId: Int by lazy { intent.getIntExtra("id", -1) }
    private val adapter by lazy { ItemAdapter(::onItemClick) }
}
```

> **Fragment에서는 `lateinit var binding`을 주의해야 합니다.** Fragment의 뷰는 Fragment 자신보다 먼저 죽습니다. `onDestroyView` 이후에 남아 있는 binding을 읽으면 이미 파괴된 뷰를 붙잡게 되어 누수가 됩니다. `var binding: X? = null`로 두고 `onDestroyView`에서 `null`을 넣는 패턴이 흔히 쓰이는 이유입니다.

## 요약 {#summary}

> **TL;DR** — `by lazy`는 컴파일러가 첫 접근에 초기화하는 `val` 전용이고 기본적으로 스레드 안전합니다. `lateinit`은 개발자가 나중에 대입하는 `var` 전용이며, primitive·nullable에는 쓸 수 없고 초기화 전 접근 시 `UninitializedPropertyAccessException`이 납니다. 바이트코드에서 `lateinit`은 평범한 nullable 필드이고, 약속을 강제하는 것은 읽는 지점에 삽입되는 null 검사입니다.

1. **초기화 주체**: `lazy`는 컴파일러가 첫 접근 시, `lateinit`은 개발자가 명시적으로.
2. **가변성**: `lazy`는 `val` 전용, `lateinit`은 `var` 전용.
3. **lateinit 제약 3가지**: `val` 불가, primitive 불가, nullable 불가. 모두 "미초기화를 `null`로 표시"하는 구현에서 나옴.
4. **스레드 안전성**: `lazy`는 기본 보장(모드 변경 가능), `lateinit`은 보장 없음.
5. **초기화 확인**: `::prop.isInitialized`. `lateinit` 전용이며 컴파일 결과는 `null` 검사.
6. **바이트코드**: nullable 필드 + 읽는 지점의 검사. public이면 getter 안에, private이면 사용처에 인라인.
7. **lazy가 `val` 전용인 이유**: `Lazy` 인터페이스에 `setValue` 연산자가 없어서. `by`의 제약이 아님.
8. **Android**: 프레임워크·DI가 넣어 주면 `lateinit`, 스스로 계산할 수 있으면 `by lazy`.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) lazy와 lateinit의 차이점은 무엇인가요?">

가장 큰 차이는 초기화를 누가 책임지느냐입니다. `by lazy`는 프로퍼티에 처음 접근하는 시점에 컴파일러가 초기화 람다를 실행하고 결과를 캐시하므로 개발자는 계산식만 넘기면 됩니다. `val` 전용이고 기본적으로 스레드 안전하며 초기화 전 접근이라는 상황 자체가 발생하지 않습니다. 반면 `lateinit`은 개발자가 어딘가에서 명시적으로 값을 대입해야 하는 `var` 전용 수정자로, 스레드 안전성 보장이 없고 대입 전에 읽으면 `UninitializedPropertyAccessException`이 발생합니다. 값을 스스로 계산할 수 있으면 `lazy`, 프레임워크나 DI가 나중에 넣어 주면 `lateinit`이 맞습니다.

</def>
<def title="Q) lateinit을 Int나 nullable 타입에 쓸 수 없는 이유는?">

`lateinit`이 "아직 초기화되지 않음"을 내부적으로 `null`로 표시하기 때문입니다. `Int`는 백킹 필드가 JVM 원시 타입(`int`)이라 `0`에서 시작하고, `0`은 정상값이므로 미초기화를 표시할 여분의 상태가 없습니다. 코틀린 타입 레벨에서는 non-null `String`도 `null`을 담을 수 없지만, `String`의 백킹 필드는 참조라서 물리적으로 `null`에서 시작한다는 점이 다릅니다. 타입이 이미 nullable이면 `null`이 "미초기화"인지 "값이 실제로 null"인지 구분할 수 없습니다. 같은 이유로 `val`에도 붙일 수 없는데, 나중에 대입한다는 전제 자체가 성립하지 않기 때문입니다. 컴파일러가 각각 `not allowed on properties of primitive types`, `not allowed on properties of a type with nullable upper bound`, `allowed only on mutable properties`로 명확히 알려 줍니다. primitive를 지연 초기화하려면 `by lazy`를 쓰거나 nullable로 선언해 직접 검사하면 됩니다.

</def>
<def title="Q) lateinit은 바이트코드로 어떻게 컴파일되나요?">

평범한 nullable 필드로 컴파일됩니다. 바이트코드 수준에서 `lateinit`이 필드가 `null`이 되는 것을 막지는 않으며, 약속을 강제하는 것은 값을 읽는 지점에 삽입되는 null 검사입니다. 프로퍼티가 public이면 생성된 getter 안에 검사가 들어가고, private이면 getter 자체가 만들어지지 않고 사용하는 자리마다 검사가 인라인됩니다. 검사에 걸리면 `Intrinsics.throwUninitializedPropertyAccessException("프로퍼티명")`이 호출되어 어떤 프로퍼티가 초기화되지 않았는지 알려 줍니다. 검사가 없었다면 그냥 `NullPointerException`이 났을 것을, 원인을 특정할 수 있는 예외로 바꿔 주는 것입니다.

</def>
<def title="Q) lazy를 var 프로퍼티에 쓸 수 없는 이유는?">

`lazy` 전용의 특별한 규칙이 아니라 위임 규약을 만족하지 못하기 때문입니다. `var` 프로퍼티를 위임하려면 delegate에 `getValue`뿐 아니라 `setValue` 연산자도 있어야 하는데, `Lazy` 인터페이스에는 `value`와 `isInitialized()`만 있고 `setValue`가 없습니다. 실제로 시도하면 `type 'Lazy<String>' has no method 'setValue(...)', so it cannot serve as a delegate for var`라는 오류가 납니다. 직접 만든 delegate에 `setValue`를 정의하면 `var`에도 얼마든지 위임할 수 있으므로, 제약은 `by` 키워드가 아니라 `Lazy` 타입에 있습니다.

</def>
<def title="Q) lateinit 프로퍼티의 초기화 여부는 어떻게 확인하나요?">

`::propertyName.isInitialized`를 사용합니다. 클래스 안에서는 `this::config.isInitialized` 형태로 씁니다. 이 문법은 `lateinit` 프로퍼티에만 사용할 수 있고 일반 프로퍼티에는 없습니다. 컴파일 결과는 backing field에 대한 단순 null 검사라 비용이 거의 없습니다. 초기화가 외부 요인에 좌우되는 상황, 예를 들어 DI 주입 시점이나 Android 생명주기에 따라 값이 들어오는 경우에 접근 전 안전 확인용으로 유용합니다.

</def>
<def title="Q) Android에서 lateinit과 lazy는 각각 언제 쓰나요?">

값을 누가 주느냐로 판단합니다. `lateinit`은 프레임워크나 DI가 나중에 값을 넣어 주는 경우에 맞습니다. `onCreate`에서 대입하는 `binding`이나 Hilt가 주입하는 `@Inject lateinit var repository`가 대표적입니다. `by lazy`는 값을 스스로 계산할 수 있으면서 비용이 있거나 사용되지 않을 수도 있을 때 적합합니다. `intent`에서 꺼내는 값이나 어댑터 생성이 여기 해당합니다. 다만 Fragment에서 `lateinit var binding`은 주의해야 하는데, 뷰가 Fragment보다 먼저 파괴되므로 `onDestroyView` 이후 접근하면 파괴된 뷰를 붙잡아 누수가 됩니다. 이 경우 nullable로 두고 `onDestroyView`에서 `null`을 대입하는 패턴을 씁니다.

</def>
</deflist>
