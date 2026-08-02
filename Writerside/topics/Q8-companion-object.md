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
<def title="Q) companion object는 바이트코드에서 어떻게 표현되나요?">

둘러싸는 클래스 내부의 `static` 중첩 클래스(`Companion`)로 컴파일되고, 그 안에 `public static final INSTANCE` 필드를 갖습니다. `object` 선언과 동일한 전략입니다. 따라서 Kotlin의 `MyClass.myCompanionFunction()` 호출은 바이트코드 수준에서 `MyClass.Companion.INSTANCE.myCompanionFunction()`이 됩니다. 즉 companion object 멤버는 진짜 static 멤버가 아니라 감춰진 객체를 거치는 인스턴스 메서드 호출이며, `@JvmStatic`은 여기에 실제 static 진입점을 하나 더 만들어 주는 역할입니다.

</def>
</deflist>
