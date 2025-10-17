# Q16) Deep Link

## Q) 16. 딥 링크는 어떻게 처리하나요?
[딥 링크](https://developer.android.com/training/app-links/deep-linking)를 통해 사용자는 URL 또는 알림과 같은 외부 소스에서 앱 내의 특정 화면이나 기능으로 직접 이동할 수 있습니다. 
딥 링크를 처리하려면 AndroidManifest.xml에 딥 링크를 정의하고 해당 activities 또는 fragments에서 수신되는 intents를 처리해야 합니다.

### 1단계: Manifest에 딥 링크 정의
딥 링킹을 활성화하려면 딥 링크를 처리할 activity에 대해 AndroidManifest.xml에서 intent filter를 선언합니다. 
intent filter는 앱이 응답하는 URL 구조 또는 scheme을 지정합니다.

```xml
<activity android:name=".MyDeepLinkActivity">
    <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data
            android:scheme="https"
            android:host="example.com"
            android:pathPrefix="/deepLink" />
    </intent-filter>
</activity>
```

* `android:scheme`: URL scheme을 지정합니다 (예: `https`).
* `android:host`: 도메인을 지정합니다 (예: `example.com`).
* `android:pathPrefix`: URL의 경로를 정의합니다 (예: `/deepLink`).

이 구성은 `https://example.com/deepLink`와 같은 URL이 `MyDeepLinkActivity`를 열도록 허용합니다.

### 2단계: Activity에서 딥 링크 처리
activity 내부에서 수신되는 intent 데이터를 검색하고 처리하여 적절한 화면으로 이동하거나 작업을 수행합니다.

```kotlin
class MyDeepLinkActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_my_deep_link)

        // Get the intent data
        val intentData: Uri? = intent?.data
        if (intentData != null) {
            val id = intentData.getQueryParameter("id") // Example: Retrieve query parameters
            navigateToFeature(id)
        }
    }

    private fun navigateToFeature(id: String?) {
        // Navigate to a specific screen based on the deep link data
        if (id != null) {
            Toast.makeText(this, "Navigating to item: $id", Toast.LENGTH_SHORT).show()

            // navigate(..) or doSomething(..)
        }
    }
}
```

### 3단계: 딥 링크 테스트
딥 링크를 테스트하려면 아래 adb 명령을 사용할 수 있습니다.

```bash
adb shell am start -a android.intent.action.VIEW \
-d "https://example.com/deepLink?id=123" \
com.example.myapp
```

이 명령은 딥 링크를 시뮬레이션하고 앱을 열어 처리합니다.

### 추가 고려 사항
* **Custom Schemes**: 내부 링크에는 custom schemes (예: `myapp://`)를 사용할 수 있지만, 더 넓은 호환성을 위해 HTTP(S) URL을 선호합니다.
* **Navigation**: 딥 링크 데이터에 따라 앱 내의 다른 activities 또는 fragments로 이동하려면 intent를 사용합니다.
* **Fallback Handling**: 딥 링크 데이터가 유효하지 않거나 불완전한 경우 앱이 해당 케이스를 처리하는지 확인합니다.
* **App Links**: 브라우저 대신 앱에서 HTTP(S) 딥 링크가 직접 열리도록 하려면 [App Links](https://developer.android.com/studio/write/app-link-indexing)를 구성합니다.

### 요약
딥 링크 처리는 AndroidManifest.xml에 URL 패턴을 정의하고 대상 activity에서 데이터를 처리하는 것을 포함합니다.

딥 링크 데이터를 추출하고 해석함으로써 사용자를 앱의 특정 기능이나 콘텐츠로 안내하여 사용자 경험과 참여도를 향상시킬 수 있습니다.

> Q) Android에서 딥 링크를 어떻게 테스트할 수 있으며, 다양한 devices 및 scenarios에서 올바르게 작동하는지 확인하기 위한 일반적인 debugging 기술들에는 어떤 것들이 있나요?