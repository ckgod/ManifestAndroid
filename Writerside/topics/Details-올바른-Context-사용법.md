# Details: 올바른 Context 사용법

## Context를 사용할 때 주의해야 할 사항은 무엇인가요?
Context는 잘못 사용하면 메모리 누수, Conflict 또는 비효율적인 리소스 처리와 같은 문제가 발생할 수 있다. 

가장 일반적인 문제 중 하나는 **Activity 또는 Fragment Context에 대한 참조를 라이프사이클 이후에도 유지**하는 것이다. 
Garbage Collector가 Context 또는 관련 리소스에 대한 메모리를 회수할 수 없기 때문에 메모리 누수가 발생할 수 있다.

예를 들어 아래 코드는 메모리 누수를 유발한다. 

```Kotlin
object Singleton {
    var context: Context? = null
}
```

컨텍스트가 필요한 수명이 긴 object에는 Application Context를 사용해야한다.

```Kotlin
object Singleton {
    lateinit var applicationContext: Context
}
```

따라서 적절한 유형의 컨텍스트를 사용하는 게 중요하다. 
잘못된 유형의 컨텍스트를 사용하면 예기치 않은 동작이 발생할 수 있다. 

- layout inflate, dialog 같은 ui 관련 작업에는 Activity Context를 사용한다.
- 라이브러리 초기화와 같은 UI 라이프사이클과 무관한 작업에는 Application Context를 사용한다.

```Kotlin
val  dialog = AlertDialog.Builder(context.getApplicationContext()) // X

val  dialog = AlertDialog.Builder(activityContext) // O
```

또 중요한 사항은 Activity 또는 Fragment가 파괴된 후에는 컨텍스트를 사용하지 않도록 하는 것이다. 
파괴된 컴포넌트에 연결된 컨텍스트에 액세스하면 해당 컨텍스트에 연결된 리소스가 더 이상 존재하지 않을 수 있으므로 Conflict나 정의되지 않은 동작이 발생할 수 있다. 

```Kotlin
val button = Button(activity)
activity.finish() // Activity는 파괴되지만 버튼은 참조를 유지한다.
```

### 백그라운드 스레드에서 컨텍스트 사용 방지
Context는 특히 리소스에 액세스하거나 UI와 상호 작용하는 메인 스레드를 위해 설계되었다. 
백그라운드 스레드에서 사용하면 예기치 않은 Conflict나 스레딩 문제가 발생할 수 있다. 
UI 관련 컨텍스트 리소스와 상호 작용하기 전에 메인 스레드로 다시 전환해야한다.

```Kotlin
viewModelScope.launch {
    val data = fetchData()
    withContext(Dispatchers.Main) {
        Toast.makeText(context, "Data fetched", Toast.LENGTH_SHORT).show()
    }
}
```

### 익명 클래스에서의 누수 발생 예시

```Kotlin
object NetworkManager {
    interface OnDataReadyCallback {
        fun onDataReady(data: String)
    }

    fun fetchData(callback: OnDataReadyCallback) {
        Handler(Looper.getMainLooper()).postDelayed({
            callback.onDataReady("서버 데이터 도착!")
        }, 2000)
    }
}

class LeakActivity : AppCompatActivity() {

    private lateinit var textView: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_leak)
        textView = findViewById(R.id.textView)

        val callback = object : NetworkManager.OnDataReadyCallback {
            override fun onDataReady(data: String) {
                // 2초 뒤, 이 코드가 실행될 때 Activity는 이미 파괴되었을 수 있다
                textView.text = data
            }
        }

        NetworkManager.fetchData(callback)
    }
}
```
1. onCreate에서 생성된 callback 익명 클래스는 LeakActivity의 textView를 사용하기 때문에, LeakActivity의 참조(Context)를 암묵적으로 갖게 된다.
2. 이 callback 객체를 앱 전체에서 살아있는 싱글톤 객체 NetworkManager에 전달한다.
3. 만약 사용자가 네트워크 요청 후 2초가 지나기 전에 화면을 전환하면 LeackActivity는 파괴된다.
4. 하지만 NetworkManager는 여전히 callback 객체를 붙들고 있고, 이 callback은 파괴되어야 할 LeakActivity를 붙들고 있다.
5. 결과적으로, 가비지 컬렉터(GC)는 LeakActivity를 메모리에서 수거하지 못하고 메모리 누수가 발생한다.

### 요약
`Context`를 효과적으로 사용하려면, 일반적인 함정을 피하기 위해 세심한 주의가 필요하다. 
- 생명주기를 넘어서 Context를 참조하지 않기: `Activity`나 `Fragment`의 생명주기보다 오래 살아남는 객체가 Context를 참조하면 메모리 누수가 발생할 수 있다.
- 상황에 맞는 올바른 타입의 Context를 선택: 작업의 목적과 범위에 따라 Context를 구분하여 사용해야 한다.
- 파괴된 컴포넌트의 Context는 사용하지 않기: 컴포넌트가 파괴된 후에는 관련 리소스가 더 이상 유효하지 않을 수 있다. 파괴된 Context에 접근하면 Conflict를 유발할 수 있다. 
- 익명 클래스와 콜백을 주의: 익명 내부 클래스나 콜백은 자신도 모르게 Context에 대한 참조를 유지할 수 있으므로, 메모리 누수의 흔한 원인이 된다. 

