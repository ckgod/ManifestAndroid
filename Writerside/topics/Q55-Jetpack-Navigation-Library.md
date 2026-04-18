# Q55) Jetpack Navigation Library

## Jetpack Navigation Library는 무엇인가요? {#what-is-jetpack-navigation}

Jetpack Navigation 라이브러리는 Android에서 앱 내 화면 전환(navigation)을 단순화하고 표준화하기 위해 제공되는 프레임워크입니다. 개발자는 화면(destination) 사이의 이동 경로와 전환을 선언적으로 정의할 수 있어, 보일러플레이트 코드를 줄이고 일관된 사용자 경험을 유지할 수 있습니다.

이 라이브러리는 Activity, Fragment, 그리고 Composable에 대한 navigation을 모두 다룰 수 있으며, deep link, back stack 관리, 화면 전환 애니메이션 같은 고급 기능까지 함께 지원합니다. Jetpack Navigation은 다음과 같은 핵심 구성 요소들이 유기적으로 협력하여 navigation을 처리합니다.

### Navigation Graph {#navigation-graph}

Navigation Graph는 앱의 destination(화면)들과 그 사이의 이동 흐름을 정의하는 XML 리소스입니다. 각 destination은 Fragment, Activity, 또는 Custom View 등 사용자가 보게 될 하나의 화면을 나타냅니다.

```xml
<?xml version="1.0" encoding="utf-8"?>
<navigation xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/nav_graph"
    app:startDestination="@id/homeFragment">

    <fragment
        android:id="@+id/homeFragment"
        android:name="com.example.app.HomeFragment"
        android:label="Home">
        <action
            android:id="@+id/action_home_to_details"
            app:destination="@id/detailsFragment" />
    </fragment>

    <fragment
        android:id="@+id/detailsFragment"
        android:name="com.example.app.DetailsFragment"
        android:label="Details" />
</navigation>
```
{title="nav_graph.xml"}

### NavHostFragment {#navhost-fragment}

NavHostFragment는 Navigation Graph를 호스팅하는 컨테이너로, 정의된 destination들을 관리하면서 사용자의 이동 흐름에 따라 컨테이너 안의 Fragment를 동적으로 교체합니다.

```xml
<androidx.fragment.app.FragmentContainerView
    android:id="@+id/nav_host_fragment"
    android:name="androidx.navigation.fragment.NavHostFragment"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    app:navGraph="@navigation/nav_graph" />
```
{title="activity_main.xml"}

### NavController {#nav-controller}

NavController는 navigation 동작과 back stack을 실제로 관리하는 객체입니다. 코드에서 destination 사이를 프로그래밍 방식으로 이동하거나 navigation 흐름을 직접 제어할 때 사용합니다.

```kotlin
class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val navController = findNavController(R.id.nav_host_fragment)
        findViewById<Button>(R.id.navigateButton).setOnClickListener {
            navController.navigate(R.id.action_home_to_details)
        }
    }
}
```
{title="MainActivity.kt"}

### Safe Args {#safe-args}

Safe Args는 destination 사이에서 타입에 안전하게 인자를 전달할 수 있도록 코드를 자동 생성해 주는 Gradle 플러그인입니다. 매번 Bundle을 직접 만들고 키와 값을 매핑할 필요가 없어집니다.

```kotlin
val action = HomeFragmentDirections.actionHomeToDetails(itemId = 42)
findNavController().navigate(action)
```
{title="Passing Data with Safe Args.kt"}

### Deep Linking {#deep-linking}

Navigation 라이브러리는 deep link를 기본적으로 지원하므로, URL이나 알림 등 외부 진입 경로에서 곧바로 특정 destination으로 진입하도록 만들 수 있습니다.

```xml
<fragment
    android:id="@+id/detailsFragment"
    android:name="com.example.app.DetailsFragment">
    <deepLink app:uri="https://example.com/details/{itemId}" />
</fragment>
```
{title="Deep Link in Navigation Graph.xml"}

### Jetpack Navigation Library의 장점 {#benefits}

1. **중앙 집중식 navigation**: 모든 navigation 흐름이 하나의 XML 그래프로 모이기 때문에 구조가 명확해지고 유지보수가 쉬워집니다.
2. **타입에 안전한 인자 전달**: Safe Args가 자동 생성한 클래스를 통해 destination 사이의 데이터 전달이 컴파일 타임에 검증됩니다.
3. **back stack 관리**: 일관된 back 동작을 프레임워크가 자동으로 처리하므로, 화면 이동 정책을 직접 구현하다 발생하는 버그가 줄어듭니다.
4. **Deep link 지원**: 외부 진입 요청을 매끄럽게 처리하여 사용자 경험을 개선합니다.
5. **Jetpack 컴포넌트와의 통합**: Fragment, ViewModel, LiveData와 자연스럽게 결합되어 수명 주기 인식형 navigation을 보장합니다.

### 요약 {#summary}

<tldr>

Jetpack Navigation 라이브러리는 navigation 경로, 화면 전환, 인자 전달을 선언적이고 중앙 집중적으로 관리할 수 있도록 해 주는 프레임워크입니다. 다른 Jetpack 컴포넌트와 자연스럽게 결합되며, deep link 지원과 Safe Args를 통한 타입 안전성, 자동화된 back stack 관리로 보일러플레이트를 줄이고 일관된 navigation 패턴을 보장합니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Jetpack Navigation 라이브러리는 back stack을 어떻게 관리하며, NavController로 이를 어떻게 프로그래밍 방식으로 조작할 수 있나요?">

Jetpack Navigation은 NavController가 내부에 `NavBackStackEntry`로 구성된 스택을 관리하여 사용자의 화면 이동 이력을 기록합니다. `navigate()`가 호출되면 새 destination이 스택의 가장 위에 push되고, 사용자가 시스템 back 버튼을 누르거나 `popBackStack()`이 호출되면 가장 위 항목이 pop되며 이전 destination으로 돌아갑니다. NavHostFragment와 함께 사용하면 이러한 흐름이 자동으로 Fragment 트랜잭션과 동기화됩니다.

프로그래밍 방식으로 back stack을 조작할 때 자주 쓰이는 API는 다음과 같습니다. `popBackStack(destinationId, inclusive)`는 특정 destination까지 한꺼번에 pop할 때 사용하며, `inclusive = true`로 두면 해당 destination 자체도 함께 제거됩니다. 또한 `navigate()`에 `NavOptions.Builder().setPopUpTo(...)`를 적용하면 새 destination으로 이동하면서 그 직전까지의 스택을 한꺼번에 정리할 수 있어, 로그인 후 메인 화면 진입처럼 "이전 화면을 모두 지우고 이동" 시나리오에 적합합니다.

이 외에도 `getBackStackEntry(destinationId)`로 특정 destination의 NavBackStackEntry를 가져와 그에 범위가 지정된 ViewModel이나 SavedStateHandle을 공유할 수 있어, 같은 navigation 그래프 안에서 화면 간 데이터 공유를 깔끔하게 구현할 수 있습니다.

</def>
<def title="Q) Safe Args란 무엇이며, Jetpack Navigation Component에서 destination 사이의 데이터 전달 시 타입 안전성을 어떻게 강화하나요?">

Safe Args는 Navigation Graph에 정의된 `<argument>`와 action 정보를 분석하여, 각 destination에 대응하는 `Directions` 클래스와 `Args` 클래스를 컴파일 타임에 자동 생성하는 Gradle 플러그인입니다. 이를 통해 destination 사이에 데이터를 전달할 때 키 문자열과 형변환을 직접 다룰 필요가 없어집니다.

전달부에서는 `HomeFragmentDirections.actionHomeToDetails(itemId = 42)`처럼 정적 메서드로 action을 만들고 `navController.navigate(action)`을 호출합니다. 이 시점에 인자의 이름과 타입이 메서드 시그니처에 박혀 있으므로, 타입이 맞지 않거나 필수 인자를 빠뜨리면 컴파일 자체가 실패합니다. 수신부에서는 Fragment에서 `by navArgs<DetailsFragmentArgs>()`로 인자를 꺼낼 수 있어, 키 오타로 인한 런타임 크래시 위험이 사라집니다.

이렇게 컴파일 타임에 인자 정의와 사용처가 함께 검증되기 때문에, Bundle 키 문자열로 데이터를 주고받던 전통적인 방식에서 발생하던 키 오타, 누락, 타입 불일치 같은 버그를 사실상 제거할 수 있습니다.

</def>
</deflist>
