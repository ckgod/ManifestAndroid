# Q52) DataBinding

## DataBinding은 어떻게 동작하나요? {#how-databinding-works}

`DataBinding`은 XML 레이아웃의 UI 컴포넌트를 앱의 데이터 소스에 직접 연결할 수 있게 해주는 Android 라이브러리입니다. `findViewById()` 같은 보일러플레이트 코드를 줄이고 UI와 데이터 모델 간의 실시간 동기화를 가능하게 하여 선언형 UI 프로그래밍을 지원합니다. 또한 UI 로직과 비즈니스 로직을 분리하는 MVVM 아키텍처의 핵심 요소로 활용됩니다.

### DataBinding 활성화 방법 {#enabling-databinding}

`build.gradle` 파일에 다음을 추가하면 DataBinding을 활성화할 수 있습니다.

```kotlin
android {
    dataBinding {
        enabled = true
    }
}
```
{title="build.gradle.kts"}

### DataBinding 동작 방식 {#how-it-works}

DataBinding은 `<layout>` 태그를 사용하는 XML 레이아웃마다 바인딩 클래스를 생성합니다. 이 클래스를 통해 View에 직접 접근하고, 바인딩 표현식(`@{}`)으로 데이터를 XML에서 직접 바인딩할 수 있습니다.

```xml
<layout xmlns:android="http://schemas.android.com/apk/res/android">
    <data>
        <variable
            name="user"
            type="com.example.User" />
    </data>

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:orientation="vertical">

        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="@{user.name}" />

        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="@{user.age}" />
    </LinearLayout>
</layout>
```
{title="activity_main.xml"}

`User` 객체를 XML 레이아웃에 바인딩하여 `user.name`, `user.age` 값을 TextView에 동적으로 표시합니다.

### 코드에서 데이터 바인딩하기 {#binding-data-in-code}

`DataBindingUtil.setContentView()`로 바인딩 클래스 인스턴스를 생성하고 데이터를 설정합니다.

```kotlin
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val binding: ActivityMainBinding =
            DataBindingUtil.setContentView(this, R.layout.activity_main)

        val user = User("Alice", 25)
        binding.user = user
    }
}

data class User(val name: String, val age: Int)
```
{title="MainActivity.kt"}

`user` 객체를 레이아웃의 데이터 소스로 설정하면 데이터가 변경될 때 UI가 자동으로 업데이트됩니다.

### DataBinding의 주요 기능 {#key-features}

**양방향 데이터 바인딩(Two-Way Data Binding)**

`@={}` 표현식을 사용하여 UI와 데이터 모델 간의 자동 동기화를 지원합니다. 폼이나 입력 필드에서 특히 유용합니다.

```xml
<EditText
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:text="@={user.name}" />
```
{title="TwoWayBinding.xml"}

**바인딩 표현식(Binding Expressions)**

XML 내에서 문자열 연결, 조건문 등 간단한 로직을 직접 작성할 수 있습니다.

```xml
<TextView
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:text="@{user.age > 18 ? `성인` : `미성년자`}" />
```
{title="BindingExpression.xml"}

**생명주기 인식(Lifecycle Awareness)**

Activity 또는 Fragment가 활성 상태일 때만 UI를 자동으로 업데이트하여 불필요한 렌더링을 방지합니다.

### DataBinding의 장단점 {#advantages-and-drawbacks}

**장점**

- **보일러플레이트 감소**: `findViewById()` 호출 및 명시적 UI 업데이트 코드가 불필요합니다.
- **실시간 UI 업데이트**: 데이터 변경 사항이 UI에 자동으로 반영됩니다.
- **선언형 UI**: XML에 로직을 이동시켜 복잡한 레이아웃을 단순화합니다.
- **테스트 용이성**: UI와 코드를 분리하여 독립적인 테스트를 가능하게 합니다.

**단점**

- **성능 오버헤드**: ViewBinding 같은 가벼운 솔루션에 비해 런타임 오버헤드가 있습니다.
- **복잡성**: 소규모 프로젝트에는 불필요한 복잡성을 초래할 수 있습니다.
- **학습 곡선**: 바인딩 표현식과 생명주기 관리에 대한 이해가 필요합니다.

### 요약 {#summary}

<tldr>
DataBinding은 XML 레이아웃에서 UI 요소를 데이터 소스에 직접 연결하여 보일러플레이트를 줄이고 선언형 UI 프로그래밍을 가능하게 합니다. 양방향 데이터 바인딩, 바인딩 표현식 등 고급 기능을 지원하여 실시간 인터랙티브 UI를 구현하는 MVVM 아키텍처에 적합하지만, 단순한 프로젝트에는 ViewBinding이 더 적절한 선택일 수 있습니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) DataBinding과 ViewBinding의 주요 차이점은 무엇이며, 각각 어떤 상황에서 선택해야 하나요?">

| 항목 | ViewBinding | DataBinding |
|------|-------------|-------------|
| 목적 | View 참조 단순화 | 데이터 기반 UI 바인딩 |
| 바인딩 표현식 | 미지원 | 지원(`@{}`, `@={}`) |
| 양방향 바인딩 | 미지원 | 지원 |
| 런타임 오버헤드 | 최소 | 있음 |
| MVVM 통합 | 제한적 | LiveData, StateFlow 연동 |

**ViewBinding**은 `findViewById()` 없이 View 참조만 필요한 단순 프로젝트에 적합합니다. **DataBinding**은 MVVM 아키텍처 기반의 복잡한 데이터 기반 UI, LiveData 또는 StateFlow 연동이 필요한 경우에 선택합니다.

</def>
<def title="Q) DataBinding이 MVVM 아키텍처에서 어떤 역할을 하며, UI 로직과 비즈니스 로직 분리에 어떻게 기여하나요?">

MVVM에서 DataBinding은 **View와 ViewModel을 직접 연결하는 접착제** 역할을 합니다.

- **View(XML)**: 바인딩 표현식으로 ViewModel의 LiveData/StateFlow를 직접 구독합니다.
- **ViewModel**: UI 관련 코드 없이 순수 데이터 로직만 포함합니다.
- **Model**: 비즈니스 로직과 데이터 레이어를 담당합니다.

```kotlin
// ViewModel에서 LiveData 노출
class UserViewModel : ViewModel() {
    val userName = MutableLiveData<String>()
}
```

```xml
<!-- XML에서 직접 바인딩 -->
<TextView android:text="@{viewModel.userName}" />
```

이를 통해 Activity/Fragment의 UI 업데이트 코드가 제거되고, ViewModel은 Android 프레임워크에 의존하지 않아 단위 테스트가 용이해집니다.

</def>
</deflist>
