# Q76) 의존성 역전과 DI

## 의존성과 결합부터 정리 {#dependency-basics}

어떤 클래스 A가 동작하기 위해 다른 객체 B를 필요로 할 때, **A는 B에 의존한다**고 말합니다. 문제는 A가 B를 **어떻게 손에 넣는가**입니다.

```kotlin
// A가 구체 클래스 B를 직접 생성하는 코드
class OrderService {
    private val repository = SqlOrderRepository()   // 직접 new
    fun place(order: Order) = repository.save(order)
}
```

이 코드에서 `OrderService`는 `SqlOrderRepository`라는 **구체 타입을 알고, 직접 생성**합니다. 그 결과:

- `SqlOrderRepository`를 다른 구현(예: `InMemoryOrderRepository`)으로 바꾸려면 `OrderService` 코드를 고쳐야 합니다.
- 테스트에서 가짜 저장소를 끼워 넣을 수 없습니다. 생성 지점이 클래스 내부에 박혀 있기 때문입니다.

이 두 문제를 구조적으로 해결하는 원리가 **의존성 역전(DIP)**, 그 원리를 실현하는 기법이 **의존성 주입(DI)**입니다. 둘은 다른 층위의 개념이며, 이 토픽의 출발점입니다.

## DIP 원리: 의존성 역전 {#dip-principle}

### 정의 {#dip-definition}

의존성 역전 원리(Dependency Inversion Principle)는 SOLID의 D에 해당하며, 두 문장으로 구성됩니다.

1. **상위 모듈은 하위 모듈에 의존해서는 안 된다. 둘 다 추상화에 의존해야 한다.**
2. **추상화는 세부 구현에 의존해서는 안 된다. 세부 구현이 추상화에 의존해야 한다.**

여기서 상위 모듈은 정책·비즈니스 로직(`OrderService`)이고, 하위 모듈은 그 정책이 사용하는 구체 도구(`SqlOrderRepository`)입니다.

### 무엇이 '역전'되는가 {#what-inverts}

일반적인 의존 방향은 **상위 모듈 → 하위 구현**입니다. 위 예시에서 `OrderService`가 `SqlOrderRepository`를 직접 가리킵니다. DIP는 둘 사이에 **인터페이스(추상화)**를 끼워, 의존 방향을 다음과 같이 바꿉니다.

```kotlin
// 추상화 — 상위 모듈이 소유하는 계약
interface OrderRepository {
    fun save(order: Order)
}

// 상위 모듈은 인터페이스에만 의존한다
class OrderService(
    private val repository: OrderRepository
) {
    fun place(order: Order) = repository.save(order)
}

// 하위 구현이 인터페이스에 의존(구현)한다
class SqlOrderRepository : OrderRepository {
    override fun save(order: Order) { /* ... */ }
}
```

역전된 결과는 **구현(`SqlOrderRepository`)이 인터페이스(`OrderRepository`)를 향해 화살표를 그리게** 된 것입니다. 상위 모듈은 더 이상 어떤 구체 클래스도 알지 못합니다.

### 왜 이것이 가치 있는가 {#why-dip}

- **교체 가능성**: 구현을 바꿔도 `OrderService`는 그대로입니다. 새 구현이 같은 인터페이스를 따르기만 하면 됩니다.
- **테스트 용이성**: 테스트에서 `OrderRepository`의 가짜 구현(fake)을 넣어 `OrderService`만 독립적으로 검증할 수 있습니다.
- **컴파일 의존성 분리**: 상위 모듈이 구현 모듈을 컴파일타임에 참조하지 않으므로, 모듈 경계를 깔끔하게 나눌 수 있습니다.

여기서 주의할 점은, DIP는 **"추상화에 의존하라"는 설계 원리일 뿐, 그 추상화의 구현체를 누가 넣어 주는지는 말하지 않는다**는 것입니다. 위 코드에서 `OrderService`는 `OrderRepository`를 생성자로 받기만 할 뿐, 실제 객체는 외부에서 와야 합니다. 그 '외부에서 넣어 주는' 메커니즘이 다음 두 절의 주제입니다.

## IoC: 제어의 역전 {#ioc-principle}

### 정의 {#ioc-definition}

제어의 역전(Inversion of Control)은 **객체가 자신의 협력 객체나 흐름을 스스로 통제하지 않고, 그 통제권을 외부(프레임워크·컨테이너·호출자)에 넘기는** 설계 원리입니다.

`OrderService` 입장에서 보면, 자신이 쓸 `OrderRepository`를 **직접 만들 권한(제어권)을 포기하고 외부에 위임**한 것입니다.

### DIP와 IoC와 DI의 관계 {#dip-ioc-di-relation}

세 용어가 자주 섞여 쓰이므로 층위를 명확히 구분합니다.

| 개념 | 층위 | 무엇을 말하는가 |
|------|------|----------------|
| DIP | 설계 원리 | 상위 모듈과 구현이 모두 추상화에 의존하라 |
| IoC | 설계 원리 | 협력 객체·흐름의 제어권을 외부로 넘겨라 |
| DI | 구현 패턴 | IoC를 실현하는 구체 기법 — 의존 객체를 외부에서 주입 |

즉 **DI는 IoC를 구현하는 한 가지 방법**입니다. IoC를 실현하는 방식에는 의존성 주입 외에도 서비스 로케이터(Service Locator) 등이 있지만, 안드로이드에서는 DI가 표준입니다.

### IoC 컨테이너 {#ioc-container}

객체의 생성과 의존성 연결을 대신 맡아 주는 주체를 **IoC 컨테이너**라고 부릅니다. 컨테이너는 "어떤 타입에 어떤 구현을 연결할지"에 대한 설정을 읽어, 객체 그래프를 만들고 필요한 곳에 주입합니다. 안드로이드의 Hilt는 Dagger 위에 빌드된 레이어이고, 실제 컨테이너 코드 생성은 Dagger가 담당합니다. 이 둘이 함께 **컴파일타임에 코드를 생성해 이 컨테이너 역할을 수행**합니다. 리플렉션 기반 런타임 컨테이너와 달리, 빌드 시점에 연결 관계가 검증되어 런타임 오류를 줄입니다.

## 생성자 주입 {#constructor-injection}

### DI의 세 가지 방식 {#three-di-methods}

의존성을 외부에서 넣어 주는 방식은 세 가지가 있습니다.

```kotlin
// 1) 생성자 주입 — 생성 시점에 의존성을 받는다
class OrderService(private val repository: OrderRepository)

// 2) 필드 주입 — 객체 생성 후 필드에 직접 채운다
//    (세터 메서드를 통해 채우면 세터 주입으로, 엄밀히는 구분되는 개념이다)
class OrderService {
    lateinit var repository: OrderRepository
}

// 3) 메서드 주입 — 특정 동작이 필요할 때 인자로 받는다
class OrderService {
    fun place(order: Order, repository: OrderRepository) { /* ... */ }
}
```

### 왜 생성자 주입을 우선하는가 {#why-constructor}

생성자 주입이 표준으로 권장되는 데에는 명확한 이유가 있습니다.

- **불변성 보장**: 의존성을 `val`로 받을 수 있어, 객체 생성 이후 의존성이 바뀌지 않습니다. 세터 주입의 `var`/`lateinit`은 도중에 교체되거나 미초기화 상태로 노출될 수 있습니다.
- **완전한 초기화 보장**: 객체가 만들어지는 순간 모든 필수 의존성이 채워져 있습니다. `lateinit` 필드 주입은 주입 전에 접근하면 `UninitializedPropertyAccessException`이 발생합니다.
- **의존성 가시화**: 생성자 시그니처만 보면 그 클래스가 무엇을 필요로 하는지 한눈에 드러납니다. 생성자 인자가 너무 많아지면 그 자체가 "이 클래스가 너무 많은 책임을 진다"는 설계 신호가 됩니다.
- **테스트 용이**: 프레임워크 없이 `OrderService(FakeRepository())`처럼 직접 생성해 테스트할 수 있습니다.

### Hilt에서의 생성자 주입 {#hilt-constructor}

Hilt에서는 생성자에 `@Inject`를 붙이면, Hilt가 그 생성자의 인자들을 스스로 채워 객체를 만들 수 있게 됩니다.

```kotlin
class OrderService @Inject constructor(
    private val repository: OrderRepository
)
```

이렇게 하면 `OrderService`를 필요로 하는 다른 객체에 Hilt가 자동으로 `OrderService` 인스턴스를 주입할 수 있습니다. 다만 **`OrderRepository`는 인터페이스라서 Hilt가 `@Inject constructor`만으로는 어떤 구현을 넣을지 알 수 없습니다.** 이 "인터페이스 → 구현" 연결을 알려 주는 것이 다음 절의 모듈입니다.

## Hilt @Binds vs @Provides {#hilt-binds-provides}

인터페이스나 외부 라이브러리 타입처럼 **`@Inject constructor`를 붙일 수 없는 타입**은, Hilt 모듈(`@Module`) 안에서 바인딩을 명시해야 합니다. 방법은 `@Binds`와 `@Provides` 두 가지입니다.

### @Binds: 인터페이스를 구현에 연결 {#binds}

`@Binds`는 **이미 Hilt가 생성할 줄 아는 구현체를, 인터페이스 타입에 연결만** 해 줍니다. 구현체가 `@Inject constructor`를 가지고 있을 때 씁니다.

```kotlin
class SqlOrderRepository @Inject constructor(
    private val db: AppDatabase
) : OrderRepository {
    override fun save(order: Order) { /* ... */ }
}

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    abstract fun bindOrderRepository(
        impl: SqlOrderRepository       // 파라미터: Hilt가 만들 줄 아는 구현
    ): OrderRepository                 // 반환 타입: 연결할 인터페이스
}
```

특징:

- 메서드가 **추상(abstract)**이며 본문이 없습니다. 모듈은 `abstract class` 또는 `interface`여야 합니다.
- 파라미터가 구현체, 반환 타입이 인터페이스입니다. Hilt는 "이 인터페이스를 요청받으면 저 구현을 주라"로 해석합니다.
- 본문 코드를 생성하지 않으므로 **`@Provides`보다 생성 코드가 가볍습니다.**

### @Provides: 객체 생성 방법을 직접 기술 {#provides}

`@Provides`는 **객체를 만드는 코드를 메서드 본문에 직접 작성**합니다. `@Inject constructor`를 붙일 수 없는 타입, 즉 외부 라이브러리 클래스나 빌더로 조립해야 하는 객체에 씁니다.

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideRetrofit(): Retrofit =
        Retrofit.Builder()
            .baseUrl("https://api.example.com/")
            .build()

    @Provides
    fun provideApi(retrofit: Retrofit): OrderApi =   // 파라미터도 주입받는다
        retrofit.create(OrderApi::class.java)
}
```

특징:

- 메서드에 **실제 생성 로직(본문)**이 있습니다. 모듈은 보통 `object`로 둡니다.
- 메서드 파라미터도 Hilt가 주입해 줍니다(`provideApi`가 `Retrofit`을 받는 것처럼).
- `Retrofit`처럼 우리가 소스를 수정해 `@Inject`를 붙일 수 없는 외부 타입에 필수적입니다.

### 언제 무엇을 쓰는가 {#binds-vs-provides-choice}

| 구분 | @Binds | @Provides |
|------|--------|-----------|
| 용도 | 인터페이스 ↔ 구현 연결 | 객체 생성 로직 직접 작성 |
| 메서드 형태 | abstract, 본문 없음 | 본문에 생성 코드 |
| 모듈 형태 | abstract class / interface | object 권장 |
| 전제 조건 | 구현체에 `@Inject constructor` 필요 | 없음 (외부 타입도 가능) |
| 생성 코드 | 더 가벼움 | 상대적으로 무거움 |

판단 기준은 단순합니다. **구현체가 `@Inject constructor`를 가질 수 있고 인터페이스에 연결만 하면 되면 `@Binds`**, **생성 과정을 우리가 코드로 기술해야 하면(외부 라이브러리·빌더 조립) `@Provides`**를 씁니다.

한 가지 제약이 있습니다. `@Binds`(추상 메서드)와 `@Provides`(구체 메서드)는 메서드 형태가 서로 달라, **한 모듈 클래스 안에 섞으면 컴파일되지 않습니다.** 둘 다 필요하면 모듈을 분리하거나, `@Provides`만 모은 `object` 모듈과 `@Binds`만 모은 `abstract class` 모듈을 따로 둡니다. (`abstract class` 모듈의 `companion object`에 `@Provides`를 넣어 static 제공으로 만드는 우회법도 있지만, 모듈 분리가 더 명확합니다.)

## 요약 {#summary}

> **TL;DR** — DIP는 상위 모듈과 구현이 모두 추상화(인터페이스)에 의존하게 해 의존 방향을 역전시키는 설계 원리이고, IoC는 객체 생성·연결의 제어권을 외부로 넘기는 원리이며, DI는 그 IoC를 실현하는 구현 기법입니다. DI는 생성자 주입을 우선해 불변성·완전 초기화·테스트 용이성을 얻고, Hilt에서는 인터페이스 연결에 `@Binds`, 외부 타입의 생성 로직 기술에 `@Provides`를 씁니다.

1. **DIP 원리**: 상위 모듈은 구현이 아닌 추상화에 의존한다. 구현이 인터페이스를 향하도록 의존 방향이 역전되어, 교체 가능성과 테스트 용이성을 얻는다.
2. **IoC**: 객체가 협력 객체·흐름의 제어권을 스스로 갖지 않고 외부 컨테이너에 위임한다. DI는 IoC를 실현하는 한 가지 기법이다.
3. **생성자 주입**: 의존성을 생성자로 받는 방식. 불변성·완전 초기화 보장, 의존성 가시화, 프레임워크 없는 테스트가 가능해 최우선으로 권장된다.
4. **Hilt @Binds vs @Provides**: 구현체에 `@Inject constructor`가 있고 인터페이스에 연결만 하면 `@Binds`(추상, 가벼움), 외부 타입처럼 생성 로직을 직접 기술해야 하면 `@Provides`(본문 보유).

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 의존성 역전 원리(DIP)에서 '역전'되는 것은 정확히 무엇인가요?">

의존 방향이 역전됩니다. 일반적으로 상위 모듈(비즈니스 로직)이 하위 구현(구체 도구)을 직접 가리키므로 의존 화살표가 상위 → 구현으로 흐릅니다. DIP는 둘 사이에 인터페이스를 끼워, 상위 모듈은 인터페이스에만 의존하고 구현이 그 인터페이스를 구현하도록 만듭니다.

그 결과 화살표가 구현 → 인터페이스 방향으로 바뀝니다. 상위 모듈은 더 이상 어떤 구체 클래스도 알지 못하므로, 구현을 교체해도 상위 모듈 코드는 변하지 않고, 테스트에서 가짜 구현을 끼워 넣을 수 있습니다.

</def>
<def title="Q) DIP, IoC, DI는 어떻게 다른가요?">

층위가 다릅니다. DIP는 "상위 모듈과 구현이 모두 추상화에 의존하라"는 설계 원리입니다. IoC는 "객체가 자신의 협력 객체나 흐름의 제어권을 스스로 갖지 말고 외부에 넘기라"는 더 넓은 설계 원리입니다.

DI(의존성 주입)는 이 IoC를 실현하는 구체적인 구현 기법으로, 의존 객체를 클래스 내부에서 생성하지 않고 외부에서 넣어 줍니다. 즉 DI는 IoC의 한 구현 방법이며, IoC를 실현하는 다른 방법으로는 서비스 로케이터 등이 있습니다. DIP가 "무엇에 의존해야 하는가(추상화)"를 말한다면, DI는 "그 의존 객체를 어떻게 공급하는가(외부 주입)"를 말합니다.

</def>
<def title="Q) 생성자 주입을 필드(세터) 주입보다 권장하는 이유는 무엇인가요?">

네 가지 이유가 있습니다. 첫째, 의존성을 `val`로 받을 수 있어 객체 생성 이후 의존성이 바뀌지 않는 불변성이 보장됩니다. 둘째, 객체가 생성되는 순간 모든 필수 의존성이 채워지므로 완전한 초기화가 보장됩니다. 필드 주입의 `lateinit`은 주입 전에 접근하면 예외가 납니다.

셋째, 생성자 시그니처만 보면 그 클래스가 무엇을 필요로 하는지 한눈에 드러나고, 인자가 과도하게 많아지면 책임 과다라는 설계 신호가 됩니다. 넷째, 프레임워크 없이 생성자에 가짜 객체를 직접 넣어 테스트할 수 있습니다.

</def>
<def title="Q) Hilt에서 @Binds와 @Provides는 각각 언제 쓰나요?">

구현체가 `@Inject constructor`를 가질 수 있고 그것을 인터페이스 타입에 연결만 하면 될 때 `@Binds`를 씁니다. `@Binds` 메서드는 추상이며 본문이 없고, 파라미터로 구현체를 받아 반환 타입인 인터페이스에 연결합니다. 모듈은 abstract class나 interface여야 하고, 생성 코드를 만들지 않아 더 가볍습니다.

`Retrofit`처럼 우리가 소스를 수정해 `@Inject`를 붙일 수 없는 외부 라이브러리 타입이거나, 빌더로 조립해 만들어야 하는 객체에는 `@Provides`를 씁니다. `@Provides` 메서드는 본문에 실제 생성 로직을 담고, 메서드 파라미터도 Hilt가 주입해 줍니다. 모듈은 보통 object로 둡니다.

</def>
<def title="Q) @Binds와 @Provides를 한 모듈에 함께 둘 수 있나요?">

같은 모듈 클래스에 그대로 섞으면 컴파일되지 않습니다. `@Binds`는 본문 없는 추상 메서드라 모듈이 abstract class/interface여야 하고, `@Provides`는 본문을 가진 구체 메서드라 메서드 형태가 서로 충돌하기 때문입니다.

해결책은 모듈을 분리하는 것입니다. `@Binds`만 모은 abstract class 모듈과 `@Provides`만 모은 object 모듈을 따로 두면 됩니다. abstract class 모듈 안에 `@Provides`를 두어야 한다면 companion object에 넣는 우회법도 있지만, 책임이 섞여 가독성이 떨어지므로 모듈을 나누는 편이 더 명확합니다.

</def>
</deflist>
