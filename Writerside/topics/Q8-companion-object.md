# Q8) companion object란 무엇인가

`companion object`는 **클래스에 딸린 싱글톤 객체**입니다. 클래스의 인스턴스가 아니라 클래스 자체에 속하는 함수와 프로퍼티를 여기에 둡니다. 다른 언어의 `static` 멤버를 대신하는 자리지만, 실제로는 객체이기 때문에 `static`이 못 하는 일까지 할 수 있습니다.

```kotlin
class Logger {
    companion object {
        fun logMessage(message: String) {
            println("Log: $message")
        }
    }
}

Logger.logMessage("Hello")   // 인스턴스 생성 없이 클래스 이름으로 호출
```

Kotlin에는 `static` 키워드가 없습니다. 그 빈자리를 `companion object`가 채웁니다.

> **왜 키워드가 아니라 객체인가** — `static` 멤버는 언어가 특별 취급하는 예외적인 존재라, 인터페이스를 구현할 수도 인자로 넘길 수도 없습니다. Kotlin은 "클래스 수준의 멤버"를 별도 문법으로 만드는 대신 **진짜 객체 하나를 클래스 안에 넣는** 방식을 택했습니다. 덕분에 클래스 수준 기능이 객체 지향의 규칙을 그대로 따릅니다.

## 주요 특성 {#characteristics}

1. **싱글톤 역할** — 한 번만 생성되며, 둘러싸는 클래스의 인스턴스 없이 멤버에 접근할 수 있습니다.
2. **private 멤버 접근** — 둘러싸는 클래스의 `private` 생성자·필드에 접근할 수 있습니다. 팩토리 메서드가 성립하는 근거입니다.
3. **인터페이스 구현 가능** — `static`과 결정적으로 갈리는 지점입니다.
4. **이름 부여 가능** — 기본은 이름이 없지만 `companion object Factory`처럼 붙일 수 있습니다.

## 팩토리 메서드 예제 {#factory}

주 생성자를 `private`으로 막고 companion object를 유일한 진입점으로 두는 패턴입니다.

```kotlin
interface Creator {
    fun printFactoryInfo()
}

class User private constructor(private val name: String) {

    fun greet() = "Hello, my name is $name"

    // 이름을 붙일 수도, 인터페이스를 구현할 수도 있다
    companion object Factory : Creator {
        private val createdUsers = mutableListOf<User>()

        fun create(name: String): User {
            val user = User(name)        // private 생성자에 접근 가능
            createdUsers.add(user)
            return user
        }

        // 둘러싸는 클래스의 private 프로퍼티에도 접근 가능
        fun listAllUsers(): List<String> = createdUsers.map { it.name }

        override fun printFactoryInfo() {
            println("User factory created ${createdUsers.size} user(s).")
        }
    }
}

fun main() {
    val user1 = User.create("skydoves")
    val user2 = User.create("Android")

    println(user1.greet())        // Hello, my name is skydoves
    println(User.listAllUsers())  // [skydoves, Android]
    User.printFactoryInfo()       // User factory created 2 user(s).
}
```

`createdUsers.map { it.name }`에서 `name`은 `User`의 `private` 프로퍼티입니다. companion object가 둘러싸는 클래스 안에 있기 때문에 접근이 허용됩니다. 바깥에 별도 팩토리 클래스를 두면 불가능한 일입니다.

## 확장 프로퍼티 붙이기 {#extension}

companion object는 실제 객체이므로 확장 함수·프로퍼티를 붙일 수 있습니다. 표준 라이브러리 타입에도 가능합니다.

```kotlin
val String.Companion.Empty: String
    get() = ""

// 사용
val fakeUser = User.createUser(name = String.Empty)
```

`String.Companion`은 표준 라이브러리가 이미 갖고 있는 companion object입니다. 여기에 `Empty`를 얹으면 `""` 리터럴보다 의도가 드러납니다. `static` 멤버였다면 이런 확장은 불가능했습니다.

## Pro Tips {#pro-tips}

### Java 상호운용과 @JvmStatic {#jvmstatic}

Kotlin에서는 `Logger.logMessage(...)`로 자연스럽게 호출되지만, Java에서 보면 사정이 다릅니다.

```java
// Java에서는 Companion 인스턴스를 거쳐야 한다
Logger.Companion.logMessage("Hello from Java");
```

companion object가 **진짜 객체**이기 때문에 생기는 결과입니다. Java 입장에서는 `Companion`이라는 중간 단계가 계속 끼어들어 관용적이지 않습니다.

`@JvmStatic`을 붙이면 컴파일러가 둘러싸는 클래스의 바이트코드에 실제 `static` 멤버를 함께 생성합니다.

```kotlin
class Logger {
    companion object {
        @JvmStatic
        fun logMessage(message: String) {
            println("Log: $message")
        }
    }
}
```

```java
// 이제 평범한 static 메서드처럼 호출된다
Logger.logMessage("Hello from Java");
```

기존 `Companion` 경로도 그대로 남으므로 Kotlin 쪽은 아무 영향이 없습니다. Java에서 호출될 API를 만든다면 붙여 두는 편이 낫습니다.

### 바이트코드로 보는 companion object {#bytecode}

`companion object`는 둘러싸는 클래스 안의 **static 중첩 클래스**로 컴파일되고, 그 안에 `public static final INSTANCE` 필드를 갖습니다. Q7에서 본 `object`와 같은 전략입니다.

그래서 Kotlin의 이 호출은

```kotlin
MyClass.myCompanionFunction()
```

바이트코드 수준에서 이렇게 됩니다.

```java
MyClass.Companion.INSTANCE.myCompanionFunction()
```

`static` 키워드 없이도 JVM에서 static과 비슷한 접근성을 얻어내는 방식이 바로 이것입니다. 그리고 Java에서 `Logger.Companion.logMessage(...)`를 써야 했던 이유도 여기서 설명됩니다 — 감춰져 있을 뿐 실제로 객체를 거치고 있었던 것입니다.

한 가지 함의가 있습니다. companion object 멤버는 **진짜 static이 아니라 객체 메서드 호출**입니다. `@JvmStatic`은 그 호출 경로를 하나 더 만들어 주는 것이지, 없던 것을 바꾸는 게 아닙니다.

### 그래서 Java의 static이란 {#what-is-static}

비교에 앞서 `static`이 무엇인지부터 짚고 갑니다. Kotlin에는 없는 키워드라 감이 흐릴 수 있습니다.

`static`을 붙인 멤버는 **개별 인스턴스가 아니라 클래스 자체에 속합니다.** 인스턴스마다 복사본이 생기지 않고 하나만 존재하며, 모든 인스턴스가 그 하나를 공유합니다.

```java
public class Counter {
    private static int count = 0;   // 클래스에 하나. 모든 인스턴스가 공유
    private final String name;      // 인스턴스마다 하나씩

    public Counter(String name) {
        this.name = name;
        count++;                    // 누가 만들든 같은 count를 증가시킨다
    }

    public static int getCount() {  // 인스턴스 없이 호출 가능
        return count;
    }
}

new Counter("a");
new Counter("b");
Counter.getCount();   // 2 — 인스턴스가 아니라 클래스 이름으로 호출
```

여기서 `static`의 성질 네 가지가 드러납니다.

1. **소속이 클래스** — `counter.getCount()`가 아니라 `Counter.getCount()`로 부릅니다.
2. **인스턴스 없이 접근** — 객체를 하나도 만들지 않아도 씁니다.
3. **모든 인스턴스가 공유** — `count`는 몇 개를 만들든 하나뿐입니다.
4. **클래스 로드 시 한 번 초기화** — 인스턴스 생성 시점과 무관합니다.

역할은 크게 셋입니다.

- **상수** — `static final`로 선언하는 클래스 수준 고정값(`Integer.MAX_VALUE`)
- **유틸리티 메서드** — 인스턴스 상태가 필요 없는 순수 기능(`Math.max()`)
- **팩토리 메서드·공유 상태** — 생성 진입점(`Integer.valueOf()`)이나 위 예제의 인스턴스 카운터

한 가지 제약이 따라옵니다. `static` 메서드는 **인스턴스 멤버에 접근할 수 없습니다.** 호출 시점에 인스턴스가 존재한다는 보장이 없으므로 `this`가 없기 때문입니다. 위 예제에서 `getCount()`는 `name`을 읽을 수 없습니다.

Kotlin에는 이 키워드가 없고, 그 역할을 `companion object`가 대신 맡습니다. 이제 둘이 어떻게 다른지 보겠습니다.

### static과 무엇이 다른가 {#vs-static}

| | Java `static` | Kotlin `companion object` |
|---|---|---|
| 정체 | 언어가 특별 취급하는 멤버 | 실제 객체 인스턴스 |
| 인터페이스 구현 | 불가 | 가능 |
| 인자로 전달 | 불가 | 가능(객체이므로) |
| 확장 함수·프로퍼티 | 불가 | 가능 |
| 이름 부여 | 해당 없음 | 가능(`companion object Factory`) |
| 클래스의 private 접근 | 가능 | 가능 |

"인터페이스를 구현할 수 있다"가 실무에서 의미를 갖는 지점은 **클래스 자체가 팩토리나 프로바이더 역할을 타입 안전하게 맡을 수 있다**는 것입니다. 위 예제의 `Factory : Creator`가 그 형태이고, `Creator`를 받는 함수에 `User.Factory`를 그대로 넘길 수 있습니다.

### 참고: Java static은 메모리 어디에 있나 {#static-memory}

비교 대상인 Java `static`이 실제로 어디에 저장되는지는 JDK 버전에 따라 다릅니다. 면접에서 자주 나오는 지점이라 정리해 둡니다.

| | JDK 7 이하 | JDK 8 이후 |
|---|---|---|
| 클래스 메타데이터 | PermGen | **Metaspace**(네이티브 메모리, 힙 밖) |
| `static` 변수 값 | PermGen | **힙**(`java.lang.Class` 객체에 붙음) |
| 크기 제한 | 고정 | OS 메모리 한도까지 자동 확장 |

JDK 7까지는 클래스 메타데이터·`static` 변수·문자열 상수 풀이 모두 힙 안의 PermGen에 있었고, 크기가 고정이라 클래스를 많이 로드하면 `OutOfMemoryError: PermGen space`가 났습니다. JDK 8에서 PermGen이 제거되면서 **클래스 메타데이터는 Metaspace로, `static` 변수 값은 힙으로** 나뉘었습니다. "static은 Metaspace에 있다"는 흔한 오해이며, Metaspace에 있는 것은 클래스 정보이고 값 자체는 힙입니다.

교과서에 나오는 **메서드 영역(Method Area)** 은 JVM 명세가 정의한 *논리적* 영역 이름입니다. 명세는 그 영역이 물리적으로 어디여야 하는지 규정하지 않고, HotSpot이 이를 PermGen으로 구현했다가 Metaspace로 바꾼 것입니다. 명세가 아니라 구현이 바뀐 것이죠.

이 관점에서 보면 companion object와의 차이가 더 선명해집니다.

- Java `static` 멤버 → 값이 힙의 `Class` 객체에 직접 붙음
- Kotlin companion object → `INSTANCE`라는 `static` 필드가 힙의 `Companion` 인스턴스를 **가리킴**

즉 companion object 쪽은 참조 하나와 객체 하나가 더 있는 구조입니다.

> **누수 관점에서 둘은 같다** — `static` 필드는 클래스가 언로드되기 전까지 살아 있는 **GC 루트**입니다. 그래서 companion object든 Java `static`이든 여기에 `Context`·`Activity`·`View`를 담아 두면 화면이 닫혀도 해제되지 않습니다. Q4에서 본 `inner class`의 `this$0` 누수와 같은 계열이며, 붙잡는 주체가 바깥 인스턴스냐 클래스냐의 차이일 뿐입니다.

### 언제 쓰나 {#when}

- **팩토리 메서드** — 주 생성자를 `private`으로 막고 생성 경로를 통제할 때. 가장 대표적인 용도입니다.
- **클래스 수준 상수** — 개념적으로 클래스 정의의 일부인 값을 모을 때.
- **인스턴스가 필요 없는 유틸리티** — 입력 유효성 검사처럼 클래스 관련 로직이지만 특정 인스턴스에 매이지 않는 함수.

반대로 **어떤 클래스에도 속하지 않는 함수라면 companion object가 아니라 최상위 함수**가 맞습니다. 클래스를 껍데기로 만들어 유틸 함수를 담는 것은 Java 습관이지 Kotlin 방식이 아닙니다.

## 요약 {#summary}

> **TL;DR** — `companion object`는 클래스 안에 선언하는 싱글톤 객체로, Kotlin에 없는 `static`의 자리를 대신합니다. 둘러싸는 클래스의 `private` 멤버에 접근할 수 있어 팩토리 메서드에 적합하고, 진짜 객체이므로 인터페이스 구현·인자 전달·확장 함수까지 됩니다. 바이트코드에서는 `Companion` static 중첩 클래스 + `INSTANCE` 필드가 되며, Java에서 자연스럽게 부르려면 `@JvmStatic`이 필요합니다.

1. **정체**: 클래스에 딸린 싱글톤 객체. 인스턴스 없이 클래스 이름으로 멤버 접근.
2. **private 접근**: 둘러싸는 클래스의 `private` 생성자·프로퍼티에 접근 가능 → 팩토리 패턴의 근거.
3. **static과의 차이**: 인터페이스 구현, 인자 전달, 확장 함수, 이름 부여가 모두 가능.
4. **Java 상호운용**: 기본은 `Logger.Companion.logMessage(...)`. `@JvmStatic`을 붙이면 진짜 static 멤버가 함께 생성됨.
5. **바이트코드**: `Companion` static 중첩 클래스 + `public static final INSTANCE`. `MyClass.f()` → `MyClass.Companion.INSTANCE.f()`.
6. **쓰지 말아야 할 때**: 클래스와 무관한 유틸 함수는 최상위 함수로. 껍데기 클래스를 만들지 말 것.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) companion object란 무엇인가요?">

클래스 내부에 선언하는 싱글톤 객체로, 클래스의 인스턴스가 아니라 클래스 자체에 속하는 함수와 프로퍼티를 담습니다. Kotlin에는 `static` 키워드가 없기 때문에 다른 언어에서 static으로 선언할 멤버(팩토리 메서드, 클래스 수준 상수 등)를 여기에 둡니다. 클래스 이름만으로 멤버에 접근할 수 있고, 클래스당 하나만 존재하며 첫 접근 시 초기화됩니다. 실제 static 멤버와 달리 객체 인스턴스이므로 인터페이스를 구현하거나 인자로 전달할 수 있습니다.

</def>
<def title="Q) companion object가 Java의 static과 다른 점은?">

가장 큰 차이는 companion object가 **실제 객체 인스턴스**라는 것입니다. 그래서 인터페이스를 구현할 수 있고, 인자로 전달할 수 있으며, 확장 함수·프로퍼티를 붙일 수도 있습니다(`val String.Companion.Empty`). 이름을 부여하는 것도 가능합니다(`companion object Factory`). Java의 `static` 멤버는 언어가 특별 취급하는 존재라 이 중 어느 것도 되지 않습니다. 반면 둘러싸는 클래스의 `private` 멤버에 접근할 수 있다는 점은 양쪽 다 동일합니다.

</def>
<def title="Q) companion object로 팩토리 메서드를 만드는 이유는?">

companion object는 둘러싸는 클래스의 `private` 멤버에 접근할 수 있기 때문입니다. 주 생성자를 `private`으로 막아 외부에서 직접 인스턴스를 만들지 못하게 하고, companion object의 `create()` 같은 함수만 유일한 생성 경로로 열어 두면 모든 인스턴스가 검증된 상태로 만들어지도록 보장할 수 있습니다. 캐싱이나 인스턴스 재사용, 생성 이력 관리 같은 로직도 이 지점에 모을 수 있습니다. 바깥에 별도의 팩토리 클래스를 두면 `private` 생성자에 접근할 수 없어 이 패턴이 성립하지 않습니다.

</def>
<def title="Q) Java에서 companion object 멤버를 호출하려면?">

기본적으로는 `Logger.Companion.logMessage("...")`처럼 `Companion` 인스턴스를 거쳐야 합니다. companion object가 실제 객체로 컴파일되기 때문입니다. Java 관점에서는 관용적이지 않으므로, 멤버에 `@JvmStatic`을 붙이면 컴파일러가 둘러싸는 클래스의 바이트코드에 진짜 `static` 멤버를 추가로 생성해 `Logger.logMessage("...")`로 호출할 수 있게 됩니다. 기존 `Companion` 경로도 그대로 남으므로 Kotlin 측 호출에는 영향이 없습니다.

</def>
<def title="Q) Java의 static 멤버는 무엇이고 어떤 역할을 하나요?">

`static`을 붙인 멤버는 개별 인스턴스가 아니라 클래스 자체에 속합니다. 인스턴스마다 복사본이 생기지 않고 하나만 존재해 모든 인스턴스가 공유하며, 객체를 만들지 않아도 클래스 이름으로 접근할 수 있습니다(`Counter.getCount()`). 초기화는 인스턴스 생성과 무관하게 클래스가 로드될 때 한 번 이루어집니다. 주된 역할은 `static final` 상수(`Integer.MAX_VALUE`), 인스턴스 상태가 필요 없는 유틸리티 메서드(`Math.max()`), 팩토리 메서드나 인스턴스 카운터 같은 공유 상태입니다. 제약으로는 `static` 메서드가 인스턴스 멤버에 접근할 수 없다는 점이 있는데, 호출 시점에 인스턴스가 존재한다는 보장이 없어 `this`가 없기 때문입니다. Kotlin에는 이 키워드가 없고 `companion object`가 그 역할을 대신합니다.

</def>
<def title="Q) Java의 static 멤버는 메모리 어디에 할당되나요?">

JDK 버전에 따라 다릅니다. JDK 7 이하에서는 클래스 메타데이터·`static` 변수·문자열 상수 풀이 모두 힙 안의 PermGen 영역에 있었고, 크기가 고정이라 클래스를 많이 로드하면 `OutOfMemoryError: PermGen space`가 발생했습니다. JDK 8에서 PermGen이 제거되면서 클래스 메타데이터는 힙 밖의 **Metaspace**(네이티브 메모리)로, `static` 변수 값은 **힙**의 `java.lang.Class` 객체로 나뉘었습니다. "static은 Metaspace에 있다"는 흔한 오해입니다. 참고로 교과서의 메서드 영역(Method Area)은 JVM 명세상의 논리적 영역이고, PermGen과 Metaspace는 HotSpot이 그것을 구현한 방식입니다. 또한 `static` 필드는 클래스가 언로드되기 전까지 GC 루트로 남으므로, Android에서 여기에 `Context`나 `Activity`를 담으면 메모리 누수의 원인이 됩니다.

</def>
<def title="Q) companion object는 바이트코드에서 어떻게 표현되나요?">

둘러싸는 클래스 내부의 `static` 중첩 클래스(`Companion`)로 컴파일되고, 그 안에 `public static final INSTANCE` 필드를 갖습니다. `object` 선언과 동일한 전략입니다. 따라서 Kotlin의 `MyClass.myCompanionFunction()` 호출은 바이트코드 수준에서 `MyClass.Companion.INSTANCE.myCompanionFunction()`이 됩니다. 즉 companion object 멤버는 진짜 static 멤버가 아니라 감춰진 객체를 거치는 인스턴스 메서드 호출이며, `@JvmStatic`은 여기에 실제 static 진입점을 하나 더 만들어 주는 역할입니다.

</def>
</deflist>
