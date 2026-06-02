# Q75) SOLID 설계 원칙

SOLID는 객체지향 설계에서 **변경에 강하고 확장하기 쉬운 구조**를 만들기 위한 다섯 가지 원칙의 머리글자입니다. 로버트 마틴(Robert C. Martin)이 정리했으며, 각각 SRP·OCP·LSP·ISP·DIP를 가리킵니다.

이 원칙들이 공통으로 겨냥하는 문제는 **결합도(coupling)**입니다. 한 곳을 고치면 멀리 떨어진 코드가 줄줄이 깨지는 구조, 한 클래스가 너무 많은 책임을 떠안아 어디를 고쳐야 할지 모르는 구조를 막는 것이 목적입니다. 안드로이드 관점에서는 ViewModel·Repository·UseCase·DI(Hilt) 설계가 모두 이 원칙들 위에서 정당화됩니다.

다섯 원칙을 하나씩 정의 → 위반 예시 → 개선 → 왜 그런가 순으로 봅니다.

## SRP: 단일 책임 원칙 {#srp}

> **단일 책임 원칙(Single Responsibility Principle)**: 하나의 클래스는 **변경되어야 할 이유가 하나뿐**이어야 합니다.

여기서 "책임"은 메서드 개수가 아니라 **변경의 축(actor)**을 뜻합니다. 요구사항을 요청하는 주체가 서로 다르면 책임이 서로 다른 것이고, 그 책임들은 분리되어야 합니다.

### 위반 예시 {#srp-bad}

아래 `UserManager`는 변경 이유가 셋입니다. (1) 사용자 검증 규칙 변경, (2) 저장 방식 변경(DB → 네트워크), (3) 로그 포맷 변경.

```kotlin
class UserManager {
    fun validate(user: User): Boolean { /* 검증 규칙 */ }
    fun save(user: User) { /* SQLite에 INSERT */ }
    fun log(message: String) { /* 파일에 기록 */ }
}
```

### 개선 {#srp-good}

변경 축마다 클래스를 나눕니다.

```kotlin
class UserValidator { fun validate(user: User): Boolean { /* ... */ } }
class UserRepository { fun save(user: User) { /* ... */ } }
class Logger { fun log(message: String) { /* ... */ } }
```

검증 규칙이 바뀌어도 저장·로그 코드는 손대지 않습니다. **왜 중요한가**: 책임이 섞여 있으면 한 가지를 고칠 때 무관한 코드까지 재컴파일·재테스트해야 하고, 의도치 않은 부작용(side effect)이 다른 책임으로 번집니다. 안드로이드에서 "ViewModel은 UI 상태만, 데이터 접근은 Repository로" 같은 레이어 분리가 바로 SRP의 적용입니다.

## OCP: 개방-폐쇄 원칙 {#ocp}

> **개방-폐쇄 원칙(Open-Closed Principle)**: 소프트웨어 요소는 **확장에는 열려 있고 수정에는 닫혀 있어야** 합니다.

새로운 동작을 추가할 때 **기존에 동작하고 검증된 코드를 고치지 않고**, 새 코드를 더하는 방식으로 확장할 수 있어야 한다는 뜻입니다. 핵심 수단은 **추상화(인터페이스/추상 클래스)와 다형성**입니다.

### 위반 예시 {#ocp-bad}

결제 수단이 늘 때마다 `when` 분기를 직접 수정해야 합니다. 새 수단을 추가하려면 이미 검증된 `pay` 함수를 매번 건드립니다.

```kotlin
class PaymentProcessor {
    fun pay(type: String, amount: Int) {
        when (type) {
            "card" -> { /* 카드 결제 */ }
            "kakao" -> { /* 카카오페이 */ }
            // 새 수단마다 여기를 수정해야 한다
        }
    }
}
```

### 개선 {#ocp-good}

결제 수단을 인터페이스로 추상화하면, 새 수단은 **새 클래스 추가만으로** 확장됩니다. `PaymentProcessor`는 더 이상 수정되지 않습니다.

```kotlin
interface PaymentMethod { fun pay(amount: Int) }

class CardPayment : PaymentMethod { override fun pay(amount: Int) { /* ... */ } }
class KakaoPayment : PaymentMethod { override fun pay(amount: Int) { /* ... */ } }

class PaymentProcessor {
    fun process(method: PaymentMethod, amount: Int) = method.pay(amount)
}
```

**왜 중요한가**: 기존 코드를 고치지 않으면 그 코드의 기존 테스트는 여전히 유효하고, 회귀(regression) 위험이 새 코드에만 국한됩니다. OCP는 보통 DIP와 함께 추상화를 통해 달성됩니다.

## LSP: 리스코프 치환 원칙 {#lsp}

> **리스코프 치환 원칙(Liskov Substitution Principle)**: 자식 타입은 부모 타입을 **대체해도 프로그램의 정확성이 깨지지 않아야** 합니다.

상속이 "is-a" 관계라고 해서 컴파일만 통과하면 되는 것이 아닙니다. 자식은 부모가 약속한 **계약(contract)**, 즉 사전 조건·사후 조건·불변식을 지켜야 합니다. 위반하면 부모 타입을 받는 코드가 자식 인스턴스에서 예기치 못하게 깨집니다.

### 위반 예시 {#lsp-bad}

`Rectangle`을 상속한 `Square`는 너비/높이를 독립적으로 설정할 수 있다는 부모의 계약을 깹니다.

```kotlin
open class Rectangle(open var width: Int, open var height: Int)

class Square(side: Int) : Rectangle(side, side) {
    override var width: Int = side
        set(value) { field = value; super.height = value }   // 높이까지 바꿔버린다
    override var height: Int = side
        set(value) { field = value; super.width = value }
}

// 부모 타입을 받는 코드의 합리적 기대
fun resize(r: Rectangle) {
    r.width = 5
    r.height = 4
    check(r.width * r.height == 20)   // Square를 넘기면 16이 되어 깨진다
}
```

### 개선 {#lsp-good}

상속 대신 별도 추상화로 모델링합니다. 정사각형과 직사각형은 코드 재사용 관계일 뿐 치환 가능한 부모-자식이 아닙니다.

```kotlin
interface Shape { fun area(): Int }
class Rectangle(val w: Int, val h: Int) : Shape { override fun area() = w * h }
class Square(val side: Int) : Shape { override fun area() = side * side }
```

**왜 중요한가**: OCP가 다형성으로 확장을 가능하게 하려면, 그 다형성이 안전해야 합니다. LSP가 깨지면 자식 타입을 구분하려는 `if (x is Square)` 분기가 다시 등장하고 OCP가 함께 무너집니다. 실무 신호로는, 자식에서 부모 메서드를 빈 구현으로 두거나 `UnsupportedOperationException`을 던진다면 LSP 위반을 의심해야 합니다.

## ISP: 인터페이스 분리 원칙 {#isp}

> **인터페이스 분리 원칙(Interface Segregation Principle)**: 클라이언트는 **자신이 사용하지 않는 메서드에 의존하도록 강요받아서는 안 됩니다.**

크고 뚱뚱한 인터페이스 하나보다, **역할별로 작게 쪼갠 인터페이스 여러 개**가 낫다는 원칙입니다. 큰 인터페이스를 구현하면, 쓰지도 않는 메서드를 빈 구현으로 채우게 되고, 그 인터페이스가 바뀔 때 무관한 구현체까지 영향을 받습니다.

### 위반 예시 {#isp-bad}

`Worker`가 모든 일을 한 인터페이스에 담으면, 로봇은 `eat()`을 구현할 이유가 없는데도 강제로 떠안습니다.

```kotlin
interface Worker {
    fun work()
    fun eat()
}

class Robot : Worker {
    override fun work() { /* ... */ }
    override fun eat() { throw UnsupportedOperationException() }   // 강요된 의존
}
```

### 개선 {#isp-good}

역할 단위로 인터페이스를 분리하면, 각 구현체는 필요한 것만 구현합니다.

```kotlin
interface Workable { fun work() }
interface Eatable { fun eat() }

class Human : Workable, Eatable {
    override fun work() { /* ... */ }
    override fun eat() { /* ... */ }
}
class Robot : Workable {
    override fun work() { /* ... */ }
}
```

**왜 중요한가**: 인터페이스가 작을수록 의존 관계가 정확해지고, 변경의 파급 범위가 줄어듭니다. Kotlin에서는 `interface`의 디폴트 메서드로 빈 구현을 강요받는 상황을 줄일 수 있지만, 그것은 분리해야 할 인터페이스를 합쳐 두는 변명이 아니라 보조 수단입니다. ISP를 지키면 LSP 위반(빈 구현·예외 던지기)이 애초에 발생할 여지가 줄어듭니다.

## DIP: 의존성 역전 원칙 {#dip}

> **의존성 역전 원칙(Dependency Inversion Principle)**: 상위 모듈은 하위 모듈에 의존해서는 안 되며, **둘 다 추상화에 의존해야** 합니다. 그리고 추상화는 구체적인 것에 의존해서는 안 됩니다.

전통적 구조에서는 상위 정책(비즈니스 로직)이 하위 세부사항(DB, 네트워크)을 직접 호출합니다. DIP는 이 의존 방향을 **추상화를 사이에 두고 역전**시킵니다. 상위 모듈이 인터페이스를 정의(소유)하고, 하위 모듈이 그 인터페이스를 구현하게 만드는 것이 핵심입니다.

### 위반 예시 {#dip-bad}

`UserService`(상위 정책)가 `SqliteUserRepository`(하위 구체 클래스)를 직접 생성·의존합니다. 저장소를 네트워크로 바꾸려면 상위 코드를 고쳐야 하고, 테스트 시 가짜 저장소로 대체하기도 어렵습니다.

```kotlin
class SqliteUserRepository { fun findById(id: Long): User { /* ... */ } }

class UserService {
    private val repo = SqliteUserRepository()   // 구체 타입에 직접 의존
    fun getUser(id: Long) = repo.findById(id)
}
```

### 개선 {#dip-good}

추상화(`UserRepository`)를 상위 모듈 쪽에서 정의하고, 구현체를 **외부에서 주입(DI)**합니다.

```kotlin
interface UserRepository { fun findById(id: Long): User }

class SqliteUserRepository : UserRepository { override fun findById(id: Long): User { /* ... */ } }

class UserService(private val repo: UserRepository) {   // 추상화에 의존, 생성자 주입
    fun getUser(id: Long) = repo.findById(id)
}
```

**왜 중요한가**: 상위 모듈이 구체 구현을 모르게 되므로, 구현 교체(SQLite → Retrofit)와 테스트 대역(fake/mock) 주입이 상위 코드 수정 없이 가능합니다. 이것이 OCP를 실현하는 메커니즘이기도 합니다. 안드로이드의 Hilt는 이 원칙을 도구로 옮긴 것입니다. `@Inject` 생성자로 의존을 주입받고, `@Binds`로 인터페이스와 구현을 연결합니다.

```kotlin
@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {
    @Binds
    abstract fun bindUserRepository(impl: SqliteUserRepository): UserRepository
}
```

> **주의**: DIP(원칙)와 DI(의존성 주입, 기법)는 다릅니다. DIP는 "추상화에 의존하라"는 설계 방향이고, DI는 그 의존을 외부에서 넣어 주는 구현 방법입니다. Hilt·Koin은 DI 도구이며, DIP를 지키기 쉽게 해 줄 뿐 DI를 쓴다고 DIP가 저절로 지켜지는 것은 아닙니다(구체 클래스를 주입하면 여전히 DIP 위반).

## 요약 {#summary}

> **TL;DR** — SOLID는 변경에 강한 객체지향 구조를 위한 다섯 원칙입니다. SRP는 클래스의 변경 이유를 하나로, OCP는 수정 없이 확장 가능하게, LSP는 자식이 부모를 안전하게 대체하게, ISP는 인터페이스를 역할별로 작게, DIP는 상위·하위가 모두 추상화에 의존하게 만듭니다. 다섯은 따로가 아니라 맞물려 작동합니다 — DIP·LSP가 다형성을 안전하게 떠받쳐야 OCP가 성립하고, SRP·ISP가 책임과 인터페이스를 잘게 나눠야 변경의 파급이 줄어듭니다.

1. **SRP(단일 책임)**: 클래스는 변경되어야 할 이유가 하나여야 한다 — 변경의 축(actor)마다 분리한다.
2. **OCP(개방-폐쇄)**: 확장에는 열고 수정에는 닫는다 — 추상화와 다형성으로 새 코드를 더해 확장한다.
3. **LSP(리스코프 치환)**: 자식은 부모의 계약을 지켜 부모를 안전하게 대체할 수 있어야 한다.
4. **ISP(인터페이스 분리)**: 쓰지 않는 메서드에 의존을 강요하지 않는다 — 인터페이스를 역할별로 작게 쪼갠다.
5. **DIP(의존성 역전)**: 상위·하위 모듈 모두 추상화에 의존한다 — 구체 구현은 외부에서 주입한다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) SRP에서 말하는 '책임'은 정확히 무엇인가요? 메서드를 적게 두라는 뜻인가요?">

아닙니다. SRP의 책임은 메서드 개수가 아니라 **변경되어야 할 이유**, 즉 변경을 요청하는 주체(actor)를 뜻합니다. 한 클래스가 검증 규칙·저장 방식·로그 포맷을 모두 담고 있으면, 이 셋은 서로 다른 이해관계자가 서로 다른 시점에 바꾸는 별개의 변경 축입니다.

이렇게 섞여 있으면 한 가지를 고칠 때 무관한 코드까지 재컴파일·재테스트해야 하고, 부작용이 다른 책임으로 번집니다. 변경 축마다 클래스를 나누면 각 변경이 한 곳에 국한됩니다. 안드로이드에서 ViewModel은 UI 상태만 다루고 데이터 접근은 Repository로 빼는 레이어 분리가 SRP의 직접적 적용입니다.

</def>
<def title="Q) OCP를 '수정에는 닫혀 있다'고 하는데, 코드를 전혀 안 고치고 기능을 추가하는 게 가능한가요?">

기존에 동작·검증된 코어 코드를 고치지 않고, 새 코드를 더하는 방식으로 확장한다는 뜻입니다. 전체 코드를 한 줄도 안 바꾼다는 뜻은 아니고, 변경의 축이 될 부분을 미리 추상화(인터페이스)로 뽑아 두는 것이 핵심입니다.

결제 수단을 `when` 분기로 처리하면 새 수단마다 검증된 함수를 수정해야 합니다. 대신 `PaymentMethod` 인터페이스로 추상화하면, 새 수단은 새 클래스를 추가하는 것만으로 확장되고 기존 프로세서 코드는 그대로입니다. 기존 코드를 안 고치므로 그 코드의 테스트는 여전히 유효하고, 회귀 위험이 새 코드에만 갇힙니다. OCP는 보통 DIP·다형성을 통해 달성됩니다.

</def>
<def title="Q) LSP 위반의 대표 사례와, 위반 여부를 알아채는 실무 신호는 무엇인가요?">

대표 사례는 정사각형-직사각형 문제입니다. `Square`를 `Rectangle`의 자식으로 두면, 너비와 높이를 독립적으로 설정할 수 있다는 부모의 계약이 깨집니다. 너비를 5, 높이를 4로 설정하면 직사각형은 넓이 20을 기대하지만, 정사각형은 한쪽을 바꿀 때 다른 쪽도 따라 바뀌어 16이 되어 부모 타입을 받는 코드가 깨집니다.

실무 신호는 두 가지입니다. 첫째, 자식이 부모 메서드를 빈 구현으로 두거나 `UnsupportedOperationException`을 던지는 경우. 둘째, 부모 타입을 받는 곳에서 `if (x is 특정자식)`으로 자식을 구분해야만 올바로 동작하는 경우입니다. 이때는 상속 대신 별도 추상화나 합성(composition)으로 모델링하는 것이 맞습니다.

</def>
<def title="Q) ISP와 SRP는 둘 다 '쪼개라'는 말처럼 들립니다. 무엇이 다른가요?">

적용 대상과 관점이 다릅니다. SRP는 **클래스(구현)**가 변경 이유를 하나만 갖도록 하는 원칙으로, 변경의 축을 기준으로 책임을 나눕니다. ISP는 **인터페이스(계약)**를 클라이언트 관점에서 나누는 원칙으로, 클라이언트가 자신이 쓰지 않는 메서드에 의존하지 않게 합니다.

즉 SRP는 "이 클래스가 너무 많은 일을 한다"를 본다면, ISP는 "이 인터페이스가 너무 많은 것을 요구해서 구현체가 쓰지도 않는 메서드를 떠안는다"를 봅니다. `Worker`에 `work()`와 `eat()`이 함께 있으면 로봇이 `eat()`을 빈 구현이나 예외로 채워야 하는데, 이를 `Workable`·`Eatable`로 분리하면 해결됩니다. ISP를 지키면 이런 빈 구현·예외 던지기가 줄어 LSP 위반의 빌미도 함께 사라집니다.

</def>
<def title="Q) DIP와 DI(의존성 주입)는 같은 말인가요? Hilt를 쓰면 DIP가 지켜지나요?">

다릅니다. DIP는 "상위·하위 모듈이 모두 추상화에 의존하라"는 **설계 원칙(방향)**이고, DI는 그 의존을 객체 외부에서 넣어 주는 **구현 기법**입니다. DIP가 목적이고 DI는 그것을 달성하는 수단 중 하나입니다.

Hilt·Koin 같은 DI 도구는 DIP를 지키기 쉽게 해 주지만, DI를 쓴다고 DIP가 저절로 지켜지지는 않습니다. 예를 들어 추상화 없이 구체 클래스(`SqliteUserRepository`)를 그대로 주입하면, 주입은 했어도 상위 모듈이 여전히 구체 타입에 의존하므로 DIP 위반입니다. DIP를 지키려면 상위 모듈 쪽에서 `UserRepository` 같은 인터페이스를 정의하고, Hilt의 `@Binds`로 구현체를 그 인터페이스에 바인딩해 주입해야 합니다.

</def>
</deflist>
