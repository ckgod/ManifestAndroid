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
            .fold({ UiState.Success(it) }, { UiState.Error })
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

## 경계와 추상화: 의존성 역전 {#boundary-and-abstraction}

도메인이 데이터를 알면 안 되는데, 동시에 데이터를 가져와야 한다는 요구는 모순처럼 보입니다. 이 모순을 푸는 장치가 **경계에서의 추상화**, 구체적으로 **의존성 역전 원칙(DIP, Dependency Inversion Principle)**입니다.

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

추상과 구현을 런타임에 연결하는 일은 **의존성 주입(DI)**이 맡습니다. 안드로이드에서는 보통 Hilt를 쓰며, **인터페이스와 구현의 연결을 가장 바깥(앱 조립 지점)에서** 선언합니다. 도메인·데이터 어느 쪽도 서로를 직접 `new` 하지 않습니다.

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

## 요약 {#summary}

> **TL;DR** — Clean Architecture는 코드를 도메인·데이터·표현 세 계층으로 나누고, 의존 방향을 항상 바깥에서 안쪽(도메인)으로만 향하게 강제합니다. 도메인은 안드로이드·Retrofit·Room 같은 세부사항을 모르는 순수 Kotlin이며, 데이터·표현이 도메인을 의존합니다. 도메인이 데이터를 알지 않으면서도 데이터를 쓰는 모순은, **인터페이스를 도메인에 두고 구현을 데이터에 두는 의존성 역전**으로 풉니다. 그 경계 연결은 DI(Hilt)가 가장 바깥에서 담당하며, 그 덕분에 테스트·구현 교체·병렬 개발이 쉬워집니다.

1. **세 계층(도메인·데이터·표현)**: 도메인은 엔티티·유스케이스·리포지토리 인터페이스를 담은 순수 Kotlin 핵심, 데이터는 그 인터페이스 구현과 외부 입출력, 표현은 ViewModel·UI·UiState.
2. **의존 규칙**: 의존 방향은 항상 안쪽으로만. 도메인은 어떤 바깥 계층도 import하지 않으며, 멀티 모듈로 컴파일 단계에서 강제할 수 있다.
3. **경계와 추상화**: 인터페이스를 도메인이 소유하고 구현을 데이터가 제공하는 의존성 역전으로 모순을 해소하고, DI가 바깥에서 둘을 연결한다.

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
</deflist>
