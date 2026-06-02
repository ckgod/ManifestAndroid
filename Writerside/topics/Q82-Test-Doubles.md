# Q82) Test Double

## Test Double란 무엇인가 {#what-is-test-double}

Test Double은 **테스트 대상(SUT, System Under Test)이 의존하는 실제 협력 객체를, 테스트를 위해 대체한 객체**를 통틀어 부르는 용어입니다. 영화에서 위험한 장면을 대신 연기하는 대역 배우(stunt double)에서 따온 이름으로, Gerard Meszaros의 *xUnit Test Patterns*에서 정립되었습니다.

실제 의존성을 그대로 쓰지 않고 대역으로 바꾸는 이유는 다음과 같습니다.

1. **느린 의존성을 빠르게**: 네트워크 호출, 디스크 I/O, DB 접근은 단위 테스트 한 건마다 수백 ms를 잡아먹습니다. 대역으로 바꾸면 메모리 안에서 즉시 끝납니다.
2. **재현하기 어려운 상황을 강제로**: "서버가 500을 반환할 때", "네트워크가 끊겼을 때" 같은 경로는 실제 의존성으로는 안정적으로 만들기 어렵습니다. 대역은 그 상황을 임의로 만들 수 있습니다.
3. **비결정성 제거**: 현재 시각, 난수, 외부 서버 상태처럼 매번 달라지는 값을 고정해, 같은 입력에 항상 같은 결과가 나오게 합니다.
4. **검증 지점 확보**: SUT가 협력 객체를 올바르게 호출했는지(어떤 인자로, 몇 번) 직접 확인하고 싶을 때가 있습니다.

Test Double은 위 목적에 따라 **Dummy / Fake / Stub / Spy / Mock** 다섯 종류로 나뉩니다. 이 중 Fake·Stub·Spy·Mock 네 가지가 실무의 핵심이며, 이들을 구분하는 기준은 **(가) 동작 구현이 있는가 (나) 검증을 상태로 하는가 행위로 하는가**입니다.

```kotlin
// 이 토픽 전반에서 쓸 SUT와 의존성
interface UserRepository {
    fun loadUser(id: String): User
    fun save(user: User)
}

class UserService(private val repo: UserRepository) {
    fun rename(id: String, newName: String) {
        val user = repo.loadUser(id)
        repo.save(user.copy(name = newName))
    }
}
```

## Stub: 정해진 답을 돌려준다 {#stub}

Stub은 **테스트 중에 받은 호출에 대해 미리 준비된 고정 값을 돌려주도록 만든 대역**입니다. SUT가 입력으로 삼을 값을 공급하는 것이 유일한 역할이며, SUT가 자신을 어떻게 호출했는지는 기록하지도 검증하지도 않습니다.

핵심은 **상태 기반 검증(state verification)을 돕는다**는 점입니다. Stub으로 입력을 고정해 두고, 테스트는 그 입력에 대해 SUT가 만들어 낸 **결과(반환값이나 SUT의 최종 상태)**를 단언합니다.

```kotlin
class StubUserRepository(private val fixed: User) : UserRepository {
    override fun loadUser(id: String): User = fixed   // 항상 같은 값
    override fun save(user: User) { /* 무시 */ }
}

@Test
fun `loadUser 결과로 화면 제목을 만든다`() {
    val repo = StubUserRepository(User(id = "1", name = "철수"))
    val service = ProfileTitleService(repo)

    val title = service.title("1")               // SUT 실행

    assertEquals("철수 님의 프로필", title)        // 결과(상태) 검증
}
```

Mockito/MockK로도 Stub을 만들 수 있습니다. `when(...).thenReturn(...)`(Mockito)이나 `every { ... } returns ...`(MockK)로 반환값만 지정하고 호출 검증을 하지 않으면, 그 객체는 사실상 Stub으로 쓰인 것입니다.

```kotlin
val repo = mockk<UserRepository>()
every { repo.loadUser("1") } returns User("1", "철수")   // 반환값만 고정 = Stub 용도
```

## Mock: 호출이 일어났는지 검증한다 {#mock}

Mock은 **SUT가 자신을 어떻게 호출해야 하는지에 대한 기대(expectation)를 미리 설정해 두고, 그 기대대로 호출됐는지를 검증하는 대역**입니다. 검증의 초점이 "결과 상태"가 아니라 "협력 객체와의 상호작용"이라는 점에서 Stub과 본질적으로 다릅니다. 이를 **행위 기반 검증(behavior verification)**이라고 합니다.

Mock이 적합한 경우는 **SUT의 효과가 반환값이 아니라 다른 객체에 대한 호출로만 드러날 때**입니다. 예를 들어 분석 이벤트 전송, 로그 기록, 저장 호출처럼 SUT가 "무언가를 했다"는 사실 자체를 검증해야 하는 상황입니다.

```kotlin
@Test
fun `rename 은 변경된 이름으로 save 를 호출한다`() {
    val repo = mockk<UserRepository>(relaxUnitFun = true)
    every { repo.loadUser("1") } returns User("1", "철수")
    val service = UserService(repo)

    service.rename("1", "영희")

    // 행위 검증: 올바른 인자로 save가 정확히 1번 호출됐는가
    verify(exactly = 1) { repo.save(User("1", "영희")) }
}
```

여기서 `repo.save(...)`는 반환값이 `Unit`이라 결과를 단언할 대상이 없습니다. 그래서 "호출됐는가"를 검증하는 Mock이 필요합니다. 반대로 `verify`를 남발해 모든 호출을 검증하면, 구현 세부에 묶인 깨지기 쉬운 테스트(fragile test)가 됩니다. 행위 검증은 **상호작용 자체가 명세인 경우**에만 쓰는 것이 원칙입니다.

## Fake: 가볍지만 진짜로 동작한다 {#fake}

Fake는 **실제와 동등하게 동작하는 구현을 갖지만, 운영에는 부적합하도록 단순화한 대역**입니다. Stub이 고정 값만 돌려주는 것과 달리, Fake는 **실제 로직을 수행**합니다. 다만 그 로직이 프로덕션용이 아닐 뿐입니다.

대표적인 예가 **인메모리 저장소**입니다. 실제 DB 대신 `MutableMap`에 데이터를 넣고 빼지만, "저장한 것을 다시 읽으면 그대로 나온다"는 저장소의 계약은 충실히 지킵니다.

```kotlin
class FakeUserRepository : UserRepository {
    private val store = mutableMapOf<String, User>()

    override fun loadUser(id: String): User =
        store[id] ?: error("user not found: $id")

    override fun save(user: User) {           // 실제로 상태가 바뀐다
        store[user.id] = user
    }
}

@Test
fun `rename 후 다시 읽으면 이름이 바뀌어 있다`() {
    val repo = FakeUserRepository()
    repo.save(User("1", "철수"))
    val service = UserService(repo)

    service.rename("1", "영희")

    assertEquals("영희", repo.loadUser("1").name)   // 상태 검증
}
```

Fake의 장점은 **여러 테스트에서 재사용 가능하고, 실제 동작에 가까워 통합적인 흐름까지 자연스럽게 검증된다**는 점입니다. Stub처럼 테스트마다 반환값을 일일이 지정할 필요가 없습니다. 안드로이드에서는 Room을 인메모리 DB(`Room.inMemoryDatabaseBuilder`)로 띄우거나, Repository 인터페이스의 Fake 구현을 두는 방식이 권장됩니다. 구글의 아키텍처 가이드도 단순 Mock보다 Fake 사용을 권장합니다.

## Spy: 실제 객체를 감싸 호출을 기록한다 {#spy}

Spy는 **실제 객체(또는 실제 동작)를 그대로 두면서, 그 위에 호출 기록·검증 기능을 덧씌운 대역**입니다. 두 가지 결이 있습니다.

첫째, **수기로 만든 Spy**는 호출 사실을 스스로 기록하는 객체입니다. Mock 프레임워크 없이 "몇 번 불렸는지, 어떤 인자로 불렸는지"를 필드에 직접 저장합니다.

```kotlin
class SpyEmailSender : EmailSender {
    val sentTo = mutableListOf<String>()      // 호출을 기록

    override fun send(address: String, body: String) {
        sentTo.add(address)                   // 실제 발송 대신 기록만
    }
}

@Test
fun `가입 시 환영 메일을 1번 보낸다`() {
    val sender = SpyEmailSender()
    SignUpService(sender).signUp("a@b.com")

    assertEquals(listOf("a@b.com"), sender.sentTo)   // 기록을 검증
}
```

둘째, **프레임워크 Spy**(MockK `spyk`, Mockito `spy`)는 **실제 구현을 그대로 호출하되, 필요한 일부 메서드만 stubbing하거나 호출 여부를 검증**할 수 있게 합니다. Mock이 기본적으로 모든 메서드를 비워(stub) 두는 것과 달리, Spy는 **기본이 실제 동작**이라는 점이 결정적 차이입니다.

```kotlin
val real = FakeUserRepository().apply { save(User("1", "철수")) }
val spy = spyk(real)                              // 실제 동작 유지

every { spy.loadUser("1") } returns User("1", "관리자")  // 이 메서드만 가짜로

val service = UserService(spy)
service.rename("1", "영희")

verify { spy.save(any()) }                        // 호출도 검증 가능
```

partial stubbing이 강력한 만큼, 어떤 메서드가 실제이고 어떤 메서드가 가짜인지 헷갈리기 쉬워 테스트 가독성을 해칠 수 있습니다. Spy는 **레거시 코드처럼 의존성을 깔끔히 분리할 수 없을 때의 절충 수단**으로 보는 것이 안전합니다.

## 언제 무엇을 쓰는가 {#choosing-which}

다섯 종류를 한 표로 정리하면 다음과 같습니다.

| 종류 | 동작 구현 | 주된 목적 | 검증 방식 |
|------|-----------|-----------|-----------|
| Dummy | 없음 (자리만 채움) | 필요 없는 인자를 채우기 | 검증 안 함 |
| Stub | 고정 값 반환 | SUT에 입력을 공급 | 상태 검증 |
| Fake | 단순화된 실제 로직 | 빠르고 실제에 가까운 협력자 | 상태 검증 |
| Spy | 실제 동작 + 기록 | 호출 기록을 남겨 검증 | 행위(또는 상태) 검증 |
| Mock | 기대 호출만(기본 비움) | 상호작용 자체를 명세·검증 | 행위 검증 |

선택의 실질적 기준은 **무엇을 검증하려는가**입니다.

- **SUT의 결과(반환값·최종 상태)를 검증**한다면, 입력을 공급하는 **Stub**이나 동작하는 **Fake**가 맞습니다. 재사용성과 실제성 때문에 **Fake를 우선** 고려합니다.
- **SUT가 협력 객체를 호출했다는 사실 자체를 검증**해야 하고, 그 효과가 반환값으로 드러나지 않는다면(예: 저장·전송·로깅) **Mock**이나 **Spy**가 맞습니다.

면접에서 자주 묻는 **Stub과 Mock의 차이**는 한 문장으로 정리됩니다. **Stub은 SUT에 값을 공급해 결과(상태)를 검증하게 하고, Mock은 SUT가 협력 객체를 어떻게 호출했는지(행위)를 검증한다.** 같은 MockK 객체라도 `every { } returns`만 쓰면 Stub 용도, `verify { }`로 호출을 단언하면 Mock 용도로 쓴 것입니다.

## 요약 {#summary}

> **TL;DR** — Test Double은 실제 의존성을 대체하는 대역의 총칭이며 Dummy/Stub/Fake/Spy/Mock로 나뉩니다. Stub은 고정 값을 공급해 결과(상태)를 검증하게 하고, Mock은 호출이 일어났는지(행위)를 검증합니다. Fake는 단순화됐지만 실제로 동작하는 구현이라 상태 검증과 재사용에 좋고, Spy는 실제 동작 위에 호출 기록을 덧씌운 대역입니다. 결과를 검증하면 Stub/Fake, 상호작용을 검증하면 Mock/Spy를 쓰며, 안드로이드에서는 Mock보다 Fake가 권장됩니다.

1. **Stub**: 받은 호출에 미리 정한 고정 값을 돌려주는 대역. SUT에 입력을 공급해 상태 기반 검증을 돕는다.
2. **Mock**: SUT가 협력 객체를 어떻게 호출해야 하는지 기대를 걸고 그대로 불렸는지 검증하는 대역. 행위 기반 검증.
3. **Fake**: 단순화됐지만 실제로 동작하는 구현(예: 인메모리 저장소). 상태 검증과 재사용에 유리하고 구글 가이드가 권장한다.
4. **Spy**: 실제 동작을 유지하면서 호출을 기록·일부 stubbing하는 대역. 기본이 실제 동작이라는 점이 Mock과 다르다.
5. **언제 무엇을**: 결과를 검증하면 Stub/Fake, 상호작용 자체를 검증하면 Mock/Spy. Stub↔Mock 차이는 상태 검증 대 행위 검증이다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Stub과 Mock의 차이를 설명해 주세요.">

둘 다 실제 의존성을 대체하지만 목적과 검증 방식이 다릅니다. Stub은 받은 호출에 미리 정한 고정 값을 돌려주는 대역으로, SUT가 입력으로 쓸 값을 공급하는 것이 역할입니다. 테스트는 그 입력에 대해 SUT가 만든 결과나 최종 상태를 단언하므로 상태 기반 검증입니다.

Mock은 SUT가 협력 객체를 어떤 인자로 몇 번 호출해야 하는지 기대를 미리 걸어 두고, 그 기대대로 호출됐는지를 검증하는 대역입니다. 검증의 초점이 결과가 아니라 상호작용이라 행위 기반 검증입니다. 같은 MockK 객체라도 `every { } returns`로 반환값만 정하면 Stub으로 쓴 것이고, `verify { }`로 호출을 단언하면 Mock으로 쓴 것입니다.

</def>
<def title="Q) Fake와 Stub은 어떻게 다른가요?">

Stub은 동작 로직이 없고 정해진 고정 값만 반환합니다. 테스트마다 어떤 호출에 어떤 값을 줄지 일일이 지정해야 합니다.

Fake는 실제와 동등하게 동작하는 구현을 갖되 운영에는 부적합하게 단순화한 대역입니다. 인메모리 저장소가 대표적으로, `save`하면 실제로 맵에 저장되고 `load`하면 그 값이 그대로 나옵니다. 즉 저장소의 계약을 충실히 지킵니다. 그래서 여러 테스트에서 재사용하기 좋고 실제 흐름에 가까운 검증이 가능합니다. 구글 아키텍처 가이드도 단순 Mock보다 Fake 사용을 권장합니다.

</def>
<def title="Q) Mock과 Spy의 차이는 무엇인가요?">

가장 큰 차이는 기본 동작입니다. Mock은 기본적으로 모든 메서드가 비워져(stub) 있어, 지정하지 않은 호출은 아무 일도 하지 않거나 기본값을 반환합니다. 객체 전체를 가짜로 만들고 그 위에 기대를 거는 방식입니다.

Spy는 기본이 실제 동작입니다. 실제 객체를 감싸 모든 메서드가 원래대로 실행되며, 그중 일부만 골라 stubbing하거나(partial stubbing) 호출 여부를 검증할 수 있습니다(MockK `spyk`, Mockito `spy`). 실제 동작은 유지하되 호출 기록만 확인하고 싶거나, 레거시 코드처럼 의존성을 깔끔히 분리하기 어려울 때 절충 수단으로 씁니다. 다만 어떤 메서드가 실제이고 어떤 메서드가 가짜인지 헷갈리기 쉬워 남용하면 가독성을 해칩니다.

</def>
<def title="Q) 단위 테스트에서 Mock보다 Fake가 권장되는 이유는 무엇인가요?">

Mock으로 모든 협력 호출을 stubbing하고 verify하면 테스트가 SUT의 구현 세부 사항에 강하게 묶입니다. 호출 순서나 내부 호출 방식만 바뀌어도 동작이 옳은데 테스트가 깨지는 깨지기 쉬운 테스트가 되기 쉽습니다.

Fake는 실제로 동작하는 단순 구현이라 SUT의 결과를 상태로 검증할 수 있습니다. 내부 호출 방식이 바뀌어도 결과만 같으면 테스트가 유지되어 리팩터링에 강합니다. 또 한 번 만든 Fake는 여러 테스트에서 재사용되고, 실제 의존성에 더 가깝게 동작해 통합적인 흐름까지 자연스럽게 검증됩니다. 이런 이유로 구글 안드로이드 아키텍처 가이드는 Mock보다 Fake를 우선 권장합니다. 다만 저장·전송처럼 효과가 반환값으로 드러나지 않고 호출 자체가 명세인 경우에는 여전히 Mock이나 Spy가 적합합니다.

</def>
<def title="Q) 어떤 협력 객체를 검증할 때 Stub 대신 Mock을 써야 하나요?">

판단 기준은 SUT의 효과가 어디로 드러나는가입니다. SUT가 협력 객체에서 값을 받아 그 값으로 결과나 상태를 만든다면, 입력을 공급하는 Stub이나 Fake로 충분하고 결과를 상태로 검증하면 됩니다.

반면 SUT의 효과가 반환값이 아니라 다른 객체에 대한 호출로만 드러날 때, 예를 들어 분석 이벤트 전송, 로그 기록, 저장소 `save` 호출처럼 반환이 `Unit`이라 단언할 결과 상태가 없는 경우에는 호출이 일어났는지를 검증하는 Mock이 필요합니다. 이때 올바른 인자로 정확한 횟수만큼 불렸는지를 `verify`로 확인합니다. 단, 검증할 필요가 없는 호출까지 모두 verify하면 깨지기 쉬운 테스트가 되므로, 상호작용 자체가 명세인 호출에만 한정해야 합니다.

</def>
</deflist>
