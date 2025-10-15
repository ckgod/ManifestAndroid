# Q12) ContentProvider

## ContentProvider {#CP-0}

`ContentProvider`는 구조화된 데이터 세트에 대한 액세스를 관리하고 애플리케이션 간에 데이터를 공유하기 위한 표준화된 인터페이스를 제공하는 구성 요소입니다. 다른 앱이나 구성 요소가 데이터를 쿼리, 삽입, 업데이트 또는 삭제하는 데 사용할 수 있는 중앙 저장소 역할을 하여 앱 전반에 걸쳐 안전하고 일관된 데이터 공유를 보장합니다.

`ContentProvider`는 여러 앱이 동일한 데이터에 액세스해야 하거나 데이터베이스 또는 내부 스토리지 구조를 노출하지 않고 다른 앱에 데이터를 제공하려는 경우에 특히 유용합니다.

### `ContentProvider`의 목적 {#CP1}

`ContentProvider`의 주된 목적은 데이터 액세스 로직을 캡슐화하여 앱 간에 데이터를 더 쉽고 안전하게 공유할 수 있도록 하는 것입니다. 이는 `SQLite` 데이터베이스, 파일 시스템 또는 네트워크 기반 데이터일 수 있는 기본 데이터 소스를 추상화하고 데이터와 상호 작용하기 위한 통합 인터페이스를 제공합니다.

### `ContentProvider`의 주요 구성 요소 {#CP2}

`ContentProvider`는 데이터 액세스를 위한 주소로 `URI (Uniform Resource Identifier)`를 사용합니다. `URI`는 다음으로 구성됩니다.

1.  **Authority**: `ContentProvider`를 식별합니다 (예: `com.example.myapp.provider`).
2.  **Path**: 데이터 유형을 지정합니다 (예: `/users` 또는 `/products`).
3.  **ID (선택 사항)**: 데이터 세트 내의 특정 항목을 나타냅니다.

### `ContentProvider` 구현하기 {#CP3}

`ContentProvider`를 생성하려면 `ContentProvider`를 서브클래스화하고 다음 메서드를 구현해야 합니다.

*   `onCreate()`: `ContentProvider`를 초기화합니다.
*   `query()`: 데이터를 검색합니다.
*   `insert()`: 새 데이터를 추가합니다.
*   `update()`: 기존 데이터를 수정합니다.
*   `delete()`: 데이터를 제거합니다.
*   `getType()`: 데이터의 `MIME type`을 반환합니다.

Figure 36. MyContentProvider.kt

```kotlin
class MyContentProvider : ContentProvider() {

    private lateinit var database: SQLiteDatabase

    override fun onCreate(): Boolean {
        database = MyDatabaseHelper(context!!).writableDatabase
        return true
    }

    override fun query(
        uri: Uri,
        projection: Array<String>?,
        selection: String?,
        selectionArgs: Array<String>?,
        sortOrder: String?
    ): Cursor? {
        return database.query(
            "users", projection, selection, selectionArgs, null, null,
            sortOrder
        )
    }

    override fun insert(uri: Uri, values: ContentValues?): Uri? {
        val id = database.insert(
            "users", null, values
        )
        return ContentUris.withAppendedId(uri, id)
    }

    override fun update(
        uri: Uri, values: ContentValues?, selection: String?,
        selectionArgs: Array<String>?
    ): Int {
        return database.update("users", values, selection, selectionArgs)
    }

    override fun delete(uri: Uri, selection: String?, selectionArgs: Array<String>?): Int {
        return database.delete("users", selection, selectionArgs)
    }

    override fun getType(uri: Uri): String? {
        return "vnd.android.cursor.dir/vnd.com.example.myapp.users"
    }
}
```

### `ContentProvider` 등록하기 {#CP4}

`ContentProvider`를 다른 앱에서 액세스할 수 있도록 하려면 `Android-Manifest.xml` 파일에 선언해야 합니다. `authority` 속성은 `ContentProvider`를 고유하게 식별합니다.

Figure 37. AndroidManifest.xml
```xml
<provider
android:name=".MyContentProvider"
android:authorities="com.example.myapp.provider"
android:exported="true"
android:grantUriPermissions="true" />
```

### `ContentProvider`에서 데이터 액세스하기 {#CP5}

다른 앱에서 `ContentProvider`와 상호 작용하려면 `ContentResolver` 클래스를 사용할 수 있습니다. `ContentResolver`는 데이터를 쿼리, 삽입, 업데이트 또는 삭제하는 메서드를 제공합니다.

Figure 38. Accessing Data from a ContentProvider

```kotlin
val contentResolver = context.contentResolver

val cursor = contentResolver.query(
    Uri.parse("content://com.example.myapp.provider/users"),
    null,
    null,
    null,
    null
)

val values = ContentValues().apply {
    put(
        "name",
        "Chang Kuk"
    )
    put(
        "email",
        "rhckdrnr123@gmail.com"
    )
}

contentResolver.insert(Uri.parse("content://com.example.myapp.provider/users"), values)
```

### `ContentProvider` 사용 사례

*   서로 다른 애플리케이션 간에 데이터 공유.
*   앱 시작 프로세스 중에 구성 요소 또는 리소스 초기화.
*   연락처, 미디어 파일 또는 앱별 데이터와 같은 구조화된 데이터에 대한 액세스 제공.
*   `Contacts` 앱 또는 `File Picker`와 같은 `Android` 시스템 기능과의 통합 활성화.
*   세분화된 보안 제어를 통한 데이터 액세스 허용.

### 요약

`ContentProvider`는 앱 간에 구조화된 데이터를 안전하고 효율적으로 공유하기 위한 중요한 구성 요소입니다. 이는 기본 데이터 스토리지 메커니즘을 추상화하면서 데이터 액세스를 위한 표준화된 인터페이스를 제공합니다. 적절한 구현 및 등록은 데이터 무결성, 보안 및 `Android` 시스템 기능과의 호환성을 보장합니다.

> Q) `ContentProvider URI`의 주요 구성 요소는 무엇이며, `ContentResolver`는 `ContentProvider`와 어떻게 상호 작용하여 데이터를 쿼리하거나 수정합니까?