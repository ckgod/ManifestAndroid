# Q19) Activity/Fragment 데이터 전달

## Activity 또는 Fragment 간에 데이터를 어떻게 전달하나요?

Activity 또는 Fragment 간의 데이터 전달은 상호작용적이고 동적인 화면을 만드는 데 중요합니다. Android는 앱 아키텍처를 준수하면서 원활한 통신을 보장하기 위해 이를 달성하기 위한 다양한 메커니즘을 제공합니다.

### Activity 간 데이터 전달

한 Activity에서 다른 Activity로 데이터를 전달하기 위해 `Intent`가 가장 일반적으로 사용되는 메커니즘입니다. 데이터는 키-값 쌍(`putExtra()`)을 사용하여 `Intent`에 추가되며, 수신 `Activity`는 `getIntent()`를 사용하여 이를 검색합니다.

```kotlin
// Sending Activity
val intent = Intent(this, SecondActivity::class.java).apply {
    putExtra("USER_NAME", "John Doe")
    putExtra("USER_AGE", 25)
}
startActivity(intent)

// Receiving Activity
class SecondActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_second)

        val userName = intent.getStringExtra("USER_NAME")
        val userAge = intent.getIntExtra("USER_AGE", 0)
        Log.d("SecondActivity", "User Name: $userName, Age: $userAge")
    }
}
```

### Fragment 간 데이터 전달

Fragment 간의 통신을 위해서는 `Bundle`을 사용할 수 있습니다. 보내는 `Fragment`는 키-값 쌍으로 `Bundle`을 생성하고 인수를 통해 받는 `Fragment`로 전달합니다.

```kotlin
// Sending Fragment
val fragment = SecondFragment().apply {
    arguments = Bundle().apply {
        putString("USER_NAME", "John Doe")
        putInt("USER_AGE", 25)
    }
}
parentFragmentManager.beginTransaction()
    .replace(R.id.fragment_container, fragment)
    .commit()

// Receiving Fragment
class SecondFragment : Fragment() {
    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        val view = inflater.inflate(R.layout.fragment_second, container, false)

        val userName = arguments?.getString("USER_NAME")
        val userAge = arguments?.getInt("USER_AGE")
        Log.d("SecondFragment", "User Name: $userName, Age: $userAge")

        return view
    }
}
```

### Jetpack Navigation 라이브러리를 사용한 Fragment 간 데이터 전달

[Jetpack Navigation](https://developer.android.com/guide/navigation) 라이브러리를 [Safe Args](https://developer.android.com/guide/navigation/use-graph/safe-args) 플러그인과 함께 사용할 때, 대상 간에 타입 안전(type-safe) 탐색을 가능하게 하는 방향(direction) 및 인수(argument) 클래스를 생성할 수 있습니다.

#### 1. 내비게이션 그래프에 인수 정의

`nav_graph.xml`에서:

```xml
<fragment
    android:id="@+id/secondFragment"
    android:name="com.example.SecondFragment">
    <argument
        android:name="username"
        app:argType="string" />
</fragment>
```

#### 2. 소스 Fragment에서 데이터 전달

`Safe Args` 플러그인은 컴파일 시점에 대상 객체(destination object)와 빌더 클래스(builder classes)를 생성하여, 아래 예시와 같이 인수를 안전하고 명시적으로 전달할 수 있도록 합니다.

```kotlin
val action = FirstFragmentDirections
    .actionFirstFragmentToSecondFragment(username = "skydoves")
findNavController().navigate(action)
```

#### 3. 대상 Fragment에서 데이터 검색

마지막으로, 전달된 인수에서 아래 코드와 같이 데이터를 검색할 수 있습니다.

```kotlin
val username = arguments?.let {
    SecondFragmentArgs.fromBundle(it).username
}
```

`Safe Args`를 사용하여 강력한 타입의 인수를 정의하고 검색함으로써 런타임 오류를 줄이고 Fragment 간의 가독성을 향상시킬 수 있습니다.

### 공유 ViewModel 사용하기

`Fragment`가 동일한 `Activity` 내에서 통신해야 할 때, 공유 `ViewModel`은 권장되는 접근 방식입니다.
공유 `ViewModel`은 동일한 `Activity` 내의 여러 `Fragment` 간에 공유되는 `ViewModel` 인스턴스를 의미합니다.
이는 `Jetpack`의 `androidx.fragment:fragment-ktx` 패키지에서 제공하는 `activityViewModels()` 메서드를 사용하여 구현됩니다.
이 메서드는 `ViewModel`의 범위를 `Activity`로 지정하여 `Fragment`가 동일한 `ViewModel` 인스턴스에 액세스하고 공유할 수 있도록 합니다.
이 방법은 `Fragment`의 긴밀한 결합을 피하고, `lifecycle-aware`하며 반응적인 데이터 공유를 가능하게 합니다.

```kotlin
// Shared ViewModel
class SharedViewModel: ViewModel() {

    private val _userData = MutableStateFlow<User?>(null)
    val userData : StateFlow<User?>
        get() = _userData

    fun setUserData(user: User) {
        _userData.value = user
    }
}

// Fragment A (Sending data)
class FirstFragment : Fragment() {
    private val sharedViewModel: SharedViewModel by activityViewModels()

    fun updateUser(user: User) {
        sharedViewModel.setUserData(user)
    }
}

// Fragment B (Receiving data on another Fragment)
class SecondFragment : Fragment() {
    private val sharedViewModel: SharedViewModel by activityViewModels()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.RESUMED) {
                sharedViewModel.userData.collectLatest { user ->
                    // ... do something with the user data
                }
            }
        }
    }
}

// Activity (Receiving data on the Activity)
class MainActivity : ComponentActivity() {
    private val sharedViewModel: SharedViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        lifecycleScope.launch {
            lifecycle.repeatOnLifecycle(Lifecycle.State.RESUMED) {
                sharedViewModel.userData.collectLatest { user ->
                    // ... do something with the user data
                }
            }
        }
    }
}
```

### 요약

각 방법에는 고유한 사용 사례가 있으며, 선택은 애플리케이션의 특정 요구 사항에 따라 달라집니다.

1.  `Intents`는 `putExtra()` 및 `getIntent()`를 사용하여 `Activities` 간에 데이터를 전달하는 데 사용됩니다.
2.  `Bundles`는 `arguments` 속성을 통해 `Fragments` 간에 데이터를 전달하는 데 일반적으로 사용됩니다.
3.  `Jetpack Navigation`을 `Safe Args` 플러그인과 함께 사용하여 생성된 `direction` 및 `argument` 클래스를 통해 `Fragment` 간에 `type-safe`한 인자 전달을 가능하게 합니다.
4.  동일한 `Activity` 내의 `Fragment` 간 데이터 공유를 위해 공유 `ViewModel`은 `lifecycle-aware`하고 느슨하게 결합된 솔루션을 제공합니다.

> Q) 공유 `ViewModel`은 동일한 `Activity` 내의 `Fragment` 간 통신을 어떻게 용이하게 하며, `Bundle` 또는 직접적인 `Fragment` 트랜잭션을 사용하는 것에 비해 어떤 장점을 제공하나요?