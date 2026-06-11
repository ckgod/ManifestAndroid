# Q77) Clean Architecture와 계층 분리

Clean Architecture는 코드를 **책임에 따라 동심원 계층으로 나누고, 의존 방향을 안쪽(정책)으로만 향하게 강제하는** 설계 원칙입니다. 안드로이드에서는 보통 도메인(domain)·데이터(data)·표현(presentation) 세 계층으로 구현합니다.

이 토픽의 핵심은 세 가지입니다. (1) 세 계층이 각각 무엇을 책임지는가, (2) 의존 규칙(dependency rule)이 왜 안쪽 방향만 허용하는가, (3) 그 규칙을 실제로 지키게 해 주는 경계(boundary)와 추상화(인터페이스·의존성 역전)는 어떻게 동작하는가.

## 세 계층: 도메인·데이터·표현 {#layers}

Clean Architecture의 계층을 안드로이드에 맞춰 구현하면 다음 세 모듈(또는 패키지)로 나뉩니다.

### 도메인 계층 {#domain-layer}

도메인(domain) 계층은 **앱의 핵심 비즈니스 규칙**을 담는 가장 안쪽 계층입니다. 다음 요소로 구성됩니다.

- **엔티티(Entity)**: 비즈니스 데이터와 규칙을 표현하는 순수 모델. 예: `User`, `Order`.
- **유스케이스(UseCase)**: 하나의 비즈니스 동작을 표현. 예: `GetUserUseCase`. 입력을 받아 리포지토리를 조합해 결과를 만듭니다.
- **리포지토리 인터페이스(Repository interface)**: 데이터를 가져오는 추상 계약. **구현이 아니라 인터페이스만** 도메인에 둡니다.

핵심 제약은 **이 계층이 안드로이드 프레임워크나 외부 라이브러리에 의존하지 않는 순수 Kotlin**이라는 점입니다. `Context`, `Retrofit`, `Room` 같은 타입이 도메인에 들어오면 안 됩니다.

```kotlin
// domain — 순수 Kotlin. 안드로이드/Retrofit/Room 타입 없음
data class User(val id: Long, val name: String)

interface UserRepository {
    suspend fun getUser(id: Long): User
}

class GetUserUseCase(private val repository: UserRepository) {
    suspend operator fun invoke(id: Long): User = repository.getUser(id)
}
```

### 데이터 계층 {#data-layer}

데이터(data) 계층은 **도메인이 선언한 리포지토리 인터페이스를 실제로 구현**하고, 외부 소스(네트워크·DB·캐시)와 통신합니다. 구성 요소는 다음과 같습니다.

- **리포지토리 구현체**: `UserRepositoryImpl`. 도메인의 `UserRepository`를 구현합니다.
- **데이터 소스(DataSource)**: 원격(Retrofit API), 로컬(Room DAO) 등 실제 입출력 담당.
- **DTO와 매퍼(Mapper)**: 네트워크/DB 모델(`UserResponse`, `UserEntity`)을 도메인 모델(`User`)로 변환합니다.

DTO와 도메인 모델을 분리하는 이유는, 서버 JSON 스키마나 DB 스키마가 바뀌어도 그 변화가 매퍼에서 흡수되어 도메인까지 번지지 않게 하기 위해서입니다.

```kotlin
// data — 도메인 인터페이스를 구현하고, 외부 기술에 의존한다
class UserRepositoryImpl(
    private val api: UserApi,           // Retrofit
) : UserRepository {
    override suspend fun getUser(id: Long): User =
        api.fetchUser(id).toDomain()    // UserResponse(DTO) → User(도메인) 매핑
}

private fun UserResponse.toDomain() = User(id = id, name = name)
```

### 표현 계층 {#presentation-layer}

표현(presentation) 계층은 **화면과 사용자 입력**을 담당합니다. 안드로이드에서는 `ViewModel` + Compose(또는 View) + UI 상태(`UiState`)로 구현합니다.

- ViewModel은 유스케이스를 호출해 결과를 받고, 이를 화면이 그릴 수 있는 `UiState`로 변환합니다.
- UI(Composable/Activity/Fragment)는 `UiState`를 구독해 렌더링하고, 사용자 이벤트를 ViewModel로 전달합니다.

ViewModel은 **도메인의 유스케이스에만 의존**하고, 데이터 계층의 구현체(`UserRepositoryImpl`, Retrofit)는 직접 알지 못합니다.

```kotlin
// presentation — 도메인(유스케이스)에만 의존한다
class UserViewModel(
    private val getUser: GetUserUseCase,
) : ViewModel() {
    private val _uiState = MutableStateFlow<UiState>(UiState.Loading)
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    fun load(id: Long) = viewModelScope.launch {
        _uiState.value = runCatching { getUser(id) }
            .fold({ UiState.Success(it) }, { UiState.Error(it.message) })  // Error는 보통 메시지를 담는다
    }
}
```

## 의존 규칙: 안쪽으로만 향한다 {#dependency-rule}

Clean Architecture의 단 하나뿐인 절대 규칙은 **의존 방향이 항상 바깥에서 안쪽으로만 향한다**는 것입니다. 안쪽일수록 더 추상적이고 변하지 않는 정책(도메인)이고, 바깥일수록 더 구체적이고 자주 바뀌는 세부사항(UI·DB·네트워크)입니다.

### 허용되는 방향과 금지되는 방향 {#allowed-direction}

- **표현 → 도메인**: 허용. ViewModel은 유스케이스를 압니다.
- **데이터 → 도메인**: 허용. 리포지토리 구현체는 도메인 인터페이스를 구현하므로 도메인을 압니다.
- **도메인 → 데이터 / 도메인 → 표현**: **금지.** 도메인은 누가 자신을 호출하는지, 데이터가 어떻게 저장되는지 알면 안 됩니다.

즉 **도메인은 어떤 바깥 계층도 import하지 않습니다.** 컴파일 의존성으로 보면, domain 모듈은 data·presentation 모듈을 의존하지 않고, 반대로 data·presentation이 domain을 의존합니다.

### 왜 이 방향이어야 하는가 {#why-direction}

이유는 **변경의 파급을 막기 위해서**입니다. UI 프레임워크(View→Compose), 네트워크 라이브러리(Retrofit→Ktor), DB(Room→SQLDelight)는 자주 교체됩니다. 의존이 안쪽으로만 흐르면, 이런 바깥 세부사항을 교체해도 도메인의 비즈니스 규칙은 컴파일조차 영향받지 않습니다.

반대로 도메인이 Retrofit 타입을 직접 참조하고 있었다면, 네트워크 라이브러리 교체가 도메인 전체를 흔들고, 도메인을 의존하는 표현 계층까지 연쇄로 깨집니다. 의존 규칙은 이 연쇄를 한 방향에서 끊는 장치입니다.

### 멀티 모듈로 규칙을 강제하기 {#enforce-with-modules}

규칙을 패키지 컨벤션으로만 두면 사람이 실수로 어길 수 있습니다. 그래서 보통 Gradle 멀티 모듈로 **컴파일 단계에서 위반을 막습니다.** `:domain` 모듈의 `build.gradle.kts`에 안드로이드·데이터 의존성을 아예 넣지 않으면, 도메인에서 `Context`나 Retrofit을 import하는 순간 컴파일이 실패합니다.

```kotlin
// :domain/build.gradle.kts — 순수 Kotlin 모듈
plugins { kotlin("jvm") }     // com.android.* 플러그인 없음

dependencies {
    implementation(libs.kotlinx.coroutines.core)
    // Retrofit, Room, androidx 의존성을 의도적으로 넣지 않는다
}
```

여기서 `kotlin("jvm")` 순수 JVM 모듈은 안드로이드 프레임워크 의존을 배제하는 가장 엄격한 버전입니다. 실무에서는 도메인이 androidx 일부(예: Paging, annotation)를 쓰기도 하는데, 그 경우에도 핵심은 `Context`·Retrofit·Room 같은 **프레임워크/구현 세부사항**을 도메인에 들이지 않는다는 원칙 자체입니다.

## 경계와 추상화: 의존성 역전 {#boundary-and-abstraction}

도메인이 데이터를 알면 안 되는데, 동시에 데이터를 가져와야 한다는 요구는 모순처럼 보입니다. 이 모순을 푸는 장치가 **경계에서의 추상화**, 구체적으로 **의존성 역전 원칙(DIP, Dependency Inversion Principle)** 입니다.

### 인터페이스를 안쪽에 두는 이유 {#interface-ownership}

핵심 기법은 **인터페이스를 사용하는 쪽(도메인)이 인터페이스를 소유하고, 구현은 바깥(데이터)에 두는 것**입니다.

- `UserRepository`라는 인터페이스를 **도메인**에 둡니다.
- `UserRepositoryImpl`이라는 구현을 **데이터**에 둡니다.

이렇게 하면 도메인은 자신이 정의한 추상(`UserRepository`)에만 의존하고, 그 구현이 무엇인지 모릅니다. 데이터 계층이 도메인의 인터페이스를 향해 의존하므로, **소스 코드 의존 방향이 런타임 호출 방향과 반대로 "역전"됩니다.** 이것이 도메인 → 데이터 호출이 필요하면서도 컴파일 의존은 데이터 → 도메인으로 유지되는 비결입니다.

```kotlin
// domain 이 인터페이스를 소유한다 (위 도메인 코드의 UserRepository)
// data 가 그 인터페이스를 구현한다 (위 데이터 코드의 UserRepositoryImpl)
// → 도메인은 구현을 import하지 않는다. 의존 방향이 역전된다.
```

### 경계에서 의존성을 주입하기 {#di-at-boundary}

추상과 구현을 런타임에 연결하는 일은 **의존성 주입(DI)** 이 맡습니다. 안드로이드에서는 보통 Hilt를 씁니다. 여기서 두 가지를 구분하면 혼동이 줄어듭니다. 바인딩을 **선언하는 위치**는 구현 옆인 데이터 계층의 `@Binds` 모듈이고, 그 바인딩이 **실제로 조립되는 시점·장소**는 앱의 Hilt 컴포넌트 그래프(`SingletonComponent`)입니다. 즉 선언은 데이터에 두되 그래프 구성은 앱 조립 지점에서 일어납니다. 도메인·데이터 어느 쪽도 서로를 직접 `new` 하지 않습니다.

```kotlin
// data 계층의 Hilt 모듈 — 추상(UserRepository)과 구현(UserRepositoryImpl)을 바인딩
@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {
    @Binds
    abstract fun bindUserRepository(impl: UserRepositoryImpl): UserRepository
}
```

`@Binds`로 `UserRepository`를 요청하면 Hilt가 `UserRepositoryImpl`을 제공합니다. ViewModel과 유스케이스는 `UserRepository`(추상)만 주입받으므로 구현을 전혀 알 필요가 없습니다.

### 경계가 주는 실질 이득 {#boundary-benefits}

경계와 추상화가 분명하면 다음이 가능해집니다.

1. **테스트 용이성**: 유스케이스 테스트에서 `UserRepository`를 가짜(fake) 구현으로 바꿔 끼울 수 있습니다. 실제 네트워크 없이 도메인 로직만 검증합니다.
2. **구현 교체**: `UserRepositoryImpl`을 캐시 우선 구현으로 바꿔도, 그 인터페이스를 쓰는 도메인·표현 코드는 한 줄도 바뀌지 않습니다.
3. **병렬 개발**: 인터페이스만 합의되면, 표현 계층과 데이터 계층을 서로 독립적으로 동시에 개발할 수 있습니다.

```kotlin
// 테스트 — 경계 덕분에 도메인 로직을 외부 없이 검증한다
class FakeUserRepository(private val user: User) : UserRepository {
    override suspend fun getUser(id: Long): User = user
}

@Test
fun `유스케이스는 리포지토리 결과를 그대로 반환한다`() = runTest {
    val useCase = GetUserUseCase(FakeUserRepository(User(1, "준호")))
    assertEquals("준호", useCase(1).name)
}
```

## 구글 공식 앱 아키텍처는 왜 다른 길을 택했나 {#vs-google-architecture}

구글의 [공식 앱 아키텍처 가이드](https://developer.android.com/topic/architecture)(UI·Domain·Data 계층)는 Clean Architecture의 안드로이드판처럼 보이지만, **의존 방향이 반대인 별개의 체계**입니다. 이 차이를 모르고 두 용어를 섞으면 설계 논의가 꼬이기 쉽습니다.

### 무엇이 다른가 {#what-differs}

| 구분 | Clean Architecture | 구글 앱 아키텍처 |
|---|---|---|
| 의존 방향 | 모든 의존이 안쪽(도메인)으로 | UI → Domain → **Data** 단방향. **도메인이 데이터를 의존** |
| Repository 인터페이스 | 도메인이 소유, 데이터가 구현(DIP) | 데이터 계층이 소유. 인터페이스 분리는 선택 |
| Domain 계층 | 시스템의 중심, 사실상 필수 | **optional** — 복잡한 로직의 재사용·캡슐화가 필요할 때만 |
| SSOT 위치 | 도메인(비즈니스 정책) | **데이터 계층**(Room·DataStore 등 영속 소스) |
| 지향점 | 프레임워크 독립, 정책 보호 | 모바일 앱 현실에 맞춘 실용성 |

가장 큰 차이는 도메인과 데이터의 관계입니다. Clean에서는 데이터가 도메인의 인터페이스를 구현하며 도메인을 향해 의존하지만, 구글 가이드에서는 유스케이스가 데이터 계층의 리포지토리를 **직접 의존**합니다. 도메인은 더 이상 가장 안쪽 보호 대상이 아니라, UI와 데이터 사이의 선택적 중간 계층입니다.

### 왜 구글은 의존 방향을 뒤집었나 {#why-google-flipped}

1. **모바일 앱의 무게중심은 데이터 처리다.** 전형적인 앱의 핵심 비즈니스 규칙(이자 계산, 재고 정책 등)은 대부분 서버에 있고, 클라이언트의 본질적 책임은 데이터를 **가져오고, 캐싱하고, 오프라인에서도 보여주고, 동기화하는 것**입니다. 그래서 구글은 보호해야 할 가장 안정적인 토대를 추상적 정책(도메인)이 아니라 데이터 계층으로 봤습니다. 가이드가 데이터 계층을 SSOT이자 출발점으로 두는 이유입니다.

2. **오프라인 우선·반응형 흐름과의 결합.** 구글 권장 패턴은 Room·DataStore 같은 영속 소스에서 `Flow`가 위로 흐르는 단방향 데이터 흐름(UDF)입니다. 데이터 계층이 "언제든 교체될 세부사항"이 아니라 앱 상태의 원천이므로, 도메인이 그것을 직접 의존하는 게 자연스러운 모델이 됩니다.

3. **보일러플레이트와 학습 비용의 절감.** DIP를 지키려면 인터페이스·구현 분리, 모듈 경계, DI 바인딩이 계층마다 필요합니다. 구글 가이드는 1인 개발부터 대규모 팀까지 모든 안드로이드 개발자에게 권장되는 **기본값**이라, 도메인을 optional로 두고 리포지토리 인터페이스도 강제하지 않습니다. 한 줄짜리 pass-through 유스케이스를 양산하느니 ViewModel이 리포지토리를 직접 쓰라는 입장입니다.

4. **교체 가능성의 현실적 평가.** Clean의 DIP가 사주는 보험은 "세부사항(DB·네트워크) 교체 시 도메인 무사"인데, 실무에서 Retrofit·Room은 사실상 표준이라 교체가 드뭅니다. 청구할 일이 적은 보험에 모든 팀이 보험료(간접 계층)를 내게 하지 않겠다는 트레이드오프입니다.

### 무엇을 얻고 무엇을 포기했나 {#tradeoff}

구글 가이드가 얻은 것은 **단순함**입니다 — 간접 계층이 적고, ViewModel·Room·Flow 같은 Jetpack 구성요소와 자연스럽게 맞물리며, 온보딩이 빠릅니다. 포기한 것은 **도메인의 프레임워크 독립성**입니다. 도메인이 데이터 계층 타입을 알게 되므로, 데이터 구현 교체나 도메인 단독 재사용의 자유는 줄어듭니다.

따라서 선택 기준은 앱의 성격입니다. 클라이언트에 복잡한 비즈니스 규칙이 실제로 존재한다면(금융 코어, 포스 시스템 등) Clean의 DIP가 여전히 유효하고, 서버 API를 표시·캐싱하는 일반적인 앱이라면 구글 가이드가 더 적은 비용으로 같은 테스트 용이성과 관심사 분리를 줍니다. 중요한 것은 어느 쪽을 따르든 **의존 방향이 어디를 향하는지 알고 선택했다고 설명할 수 있는 것**입니다.

## 요약 {#summary}

> **TL;DR** — Clean Architecture는 코드를 도메인·데이터·표현 세 계층으로 나누고, 의존 방향을 항상 바깥에서 안쪽(도메인)으로만 향하게 강제합니다. 도메인은 안드로이드·Retrofit·Room 같은 세부사항을 모르는 순수 Kotlin이며, 데이터·표현이 도메인을 의존합니다. 도메인이 데이터를 알지 않으면서도 데이터를 쓰는 모순은, **인터페이스를 도메인에 두고 구현을 데이터에 두는 의존성 역전**으로 풉니다. 그 경계 연결은 DI(Hilt)가 가장 바깥에서 담당하며, 그 덕분에 테스트·구현 교체·병렬 개발이 쉬워집니다.

1. **세 계층(도메인·데이터·표현)**: 도메인은 엔티티·유스케이스·리포지토리 인터페이스를 담은 순수 Kotlin 핵심, 데이터는 그 인터페이스 구현과 외부 입출력, 표현은 ViewModel·UI·UiState.
2. **의존 규칙**: 의존 방향은 항상 안쪽으로만. 도메인은 어떤 바깥 계층도 import하지 않으며, 멀티 모듈로 컴파일 단계에서 강제할 수 있다.
3. **경계와 추상화**: 인터페이스를 도메인이 소유하고 구현을 데이터가 제공하는 의존성 역전으로 모순을 해소하고, DI가 바깥에서 둘을 연결한다.
4. **구글 앱 아키텍처와의 구분**: 구글 공식 가이드는 도메인이 데이터를 의존하는 반대 방향의 별개 체계다. 모바일 앱의 무게중심이 데이터 처리(SSOT·오프라인 우선)라는 판단과 보일러플레이트 절감을 위해 DIP 대신 단순함을 택했다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Clean Architecture의 세 계층(도메인·데이터·표현)은 각각 무엇을 책임지나요?">

도메인 계층은 앱의 핵심 비즈니스 규칙을 담는 가장 안쪽 계층으로, 엔티티(순수 모델), 유스케이스(하나의 비즈니스 동작), 그리고 리포지토리 인터페이스로 구성됩니다. 안드로이드 프레임워크나 Retrofit·Room 같은 외부 기술에 의존하지 않는 순수 Kotlin이라는 점이 핵심 제약입니다.

데이터 계층은 도메인이 선언한 리포지토리 인터페이스를 실제로 구현하고, 원격(Retrofit)·로컬(Room) 데이터 소스와 통신하며, DTO를 도메인 모델로 변환하는 매퍼를 둡니다. 표현 계층은 ViewModel·UI·UiState로 화면과 사용자 입력을 담당하며, 도메인의 유스케이스만 호출하고 데이터 구현체는 직접 알지 못합니다.

</def>
<def title="Q) 의존 규칙(dependency rule)이란 무엇이고, 왜 안쪽 방향만 허용하나요?">

의존 규칙은 소스 코드의 의존 방향이 항상 바깥에서 안쪽(도메인)으로만 향해야 한다는 원칙입니다. 표현은 도메인을 의존하고 데이터도 도메인을 의존하지만, 도메인은 데이터나 표현을 import하지 않습니다.

이렇게 강제하는 이유는 변경의 파급을 막기 위해서입니다. UI 프레임워크, 네트워크 라이브러리, DB 같은 바깥 세부사항은 자주 교체되는데, 의존이 안쪽으로만 흐르면 이들을 교체해도 도메인의 비즈니스 규칙은 컴파일조차 영향받지 않습니다. 반대로 도메인이 Retrofit 타입을 참조하고 있었다면 라이브러리 교체가 도메인과 그것을 의존하는 표현 계층까지 연쇄로 깨뜨립니다. 보통 Gradle 멀티 모듈로 domain 모듈에 안드로이드 의존성을 아예 넣지 않아 컴파일 단계에서 위반을 막습니다.

</def>
<def title="Q) 도메인이 데이터 계층을 알면 안 되는데 어떻게 데이터를 가져오나요?">

의존성 역전 원칙(DIP)으로 해결합니다. 데이터를 가져오는 리포지토리 인터페이스(`UserRepository`)를 사용하는 쪽인 도메인에 두고, 그 구현(`UserRepositoryImpl`)은 바깥인 데이터 계층에 둡니다.

그러면 도메인은 자신이 정의한 추상에만 의존하고 구현이 무엇인지 모릅니다. 데이터 계층이 도메인의 인터페이스를 향해 의존하게 되므로, 소스 코드 의존 방향이 런타임 호출 방향(도메인이 리포지토리를 호출)과 반대로 역전됩니다. 즉 도메인 → 데이터 호출이 필요하면서도 컴파일 의존은 데이터 → 도메인으로 유지됩니다.

</def>
<def title="Q) 추상(인터페이스)과 실제 구현은 런타임에 어떻게 연결되나요?">

의존성 주입(DI)이 연결합니다. 안드로이드에서는 보통 Hilt를 쓰며, 인터페이스와 구현의 바인딩을 앱 조립 지점인 가장 바깥에서 선언합니다. 예를 들어 데이터 계층의 Hilt 모듈에서 `@Binds`로 `UserRepository`를 요청하면 `UserRepositoryImpl`을 제공하도록 바인딩합니다.

이렇게 하면 ViewModel과 유스케이스는 추상인 `UserRepository`만 주입받고 구현을 전혀 알 필요가 없습니다. 도메인과 데이터 어느 쪽도 서로를 직접 생성하지 않고, 연결 책임만 가장 바깥의 DI 설정으로 모입니다.

</def>
<def title="Q) 이렇게 계층을 나누고 경계를 두면 실질적으로 무엇이 좋아지나요?">

세 가지 이득이 있습니다. 첫째, 테스트가 쉬워집니다. 유스케이스 테스트에서 리포지토리 인터페이스를 가짜(fake) 구현으로 바꿔 끼우면 실제 네트워크 없이 도메인 로직만 검증할 수 있습니다. 둘째, 구현 교체가 안전합니다. 리포지토리 구현을 캐시 우선 방식으로 바꿔도 그 인터페이스를 쓰는 도메인·표현 코드는 바뀌지 않습니다.

셋째, 병렬 개발이 가능합니다. 인터페이스만 합의되면 표현 계층과 데이터 계층을 서로 독립적으로 동시에 개발할 수 있습니다. 이 모든 이득은 계층 사이에 명확한 경계와 추상화가 있어서, 한 계층의 변경이 다른 계층으로 새어 나가지 않기 때문에 가능합니다.

</def>
<def title="Q) 구글 공식 앱 아키텍처는 Clean Architecture와 무엇이 다르고, 왜 그렇게 설계됐나요?">

가장 큰 차이는 의존 방향입니다. Clean은 데이터 계층이 도메인의 리포지토리 인터페이스를 구현하며 안쪽(도메인)을 향해 의존하지만(DIP), 구글 가이드는 UI → Domain → Data 순서로 **도메인이 데이터 계층을 직접 의존**합니다. 도메인 계층 자체도 필수가 아니라 복잡한 로직 재사용이 필요할 때만 두는 optional 계층이고, SSOT는 도메인 정책이 아니라 데이터 계층(Room·DataStore)에 둡니다.

구글이 방향을 뒤집은 이유는 모바일 앱의 현실 때문입니다. 핵심 비즈니스 규칙은 대부분 서버에 있고 클라이언트의 본질은 데이터를 가져와 캐싱·동기화·표시하는 것이므로, 보호할 토대를 데이터 계층으로 봤습니다. 또한 모든 규모의 팀에 권장하는 기본값 가이드로서, DIP가 요구하는 인터페이스·바인딩 보일러플레이트와 pass-through 유스케이스 양산을 피하는 실용적 선택을 했습니다. 대신 도메인의 프레임워크 독립성은 포기했으므로, 클라이언트에 복잡한 비즈니스 규칙이 실재하는 앱이라면 Clean의 DIP가 여전히 유효합니다.

</def>
</deflist>
