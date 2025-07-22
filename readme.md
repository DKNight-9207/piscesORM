# Pisces ORM

## 💡 Design Philosophy

Chinese ver. ->[中文版](#chinese-readme)

When we load data from a JSON file using `json.load(f)`, the file doesn't need to remain open—we can access the data anytime. However, many ORM frameworks still require a persistent Session object during data queries. Personally, I find this design unintuitive and overly cumbersome.

Before getting into database systems, I (and perhaps many others) used JSON for data storage. That’s why I aimed to design this ORM to mimic JSON-style context management. As a result, Pisces ORM performs queries in a **session-free** manner: all data is fetched and packed at once. While this approach may incur higher memory usage, my goal is to prioritize **simplicity, ease of use, and approachability**, allowing anyone to build projects efficiently.

The name "Pisces" reflects the dual-mode nature of the ORM—supporting **both synchronous and asynchronous** APIs under consistent naming conventions. Switching between modes is as simple as choosing a different engine, with no learning curve. (I originally wanted to call it Gemini, but Google already took that for its AI... luckily, Pisces was still available)

## ✨ Features

* Session-free data fetching: objects are fully populated in a single query.
* Dual support for synchronous and asynchronous methods with unified API names.
* Easy-to-update database schema: ideal for early-stage projects with evolving database structures.

  > ⚠️ Note: Not recommended for production use yet due to missing validations and protections.

## 🔭 Roadmap

* Support for databases beyond SQLite.
* Implement a user-friendly **pessimistic locking** mechanism that allows automatic row locking during queries—even in async mode—to ensure atomicity with SQLite in single-application environments.

//////////////////////////////////////////////////////////////////////////////////////////////////////////////
<a name="chinese-readme"></a>
# 雙魚座 ORM
## 💡 設計理念：
在使用 `json.load(f)` 讀取 JSON 資料時，我們不需要持續維持檔案開啟狀態，資料也能隨時調用。然而，許多 ORM 框架在存取資料時卻仍需倚賴 Session 的存在。至少對我而言，這種設計既不直覺，也相當繁瑣。

或許有不少人跟我一樣，在接觸資料庫系統前，是透過 JSON 儲存資料。因此，我希望這個 ORM 框架的使用方式，能夠更貼近 JSON 處理的上下文管理邏輯。也因此，雙魚座 ORM 採取無 Session 依賴的查詢模式，一次性將所需資料打包完成。雖然這可能會帶來較高的記憶體使用等硬體成本，但我更希望它能以「簡單、輕鬆、易上手」為出發點，讓所有人都能快速應用在自己的專案中。

命名為「雙魚座」的原因，是因為它同時支援同步與非同步兩種操作模式，並且保有一致的 API 命名方式。你只需選擇不同的引擎，即可切換模式，使用上不會產生額外的負擔。（其實原本想叫雙子座，但「Gemini」已經被 Google 的 AI 用走了，幸好還有雙魚座可用）

## ✨ ORM特點：
* 查詢時物件一次性打包完成，完全不依賴 Session。
* 同步與非同步方法皆有提供，且命名一致。
* 支援動態更新資料庫結構，對於開發初期結構尚未穩定的專案十分友好。

  > ⚠️ 注意：由於目前缺乏某些驗證與保護機制，不建議用於正式生產環境。

## 🔭 未來計畫：
* 支援除 SQLite 外的其他資料庫系統。
* 設計簡易配置的「悲觀鎖」機制，讓搜尋時可自動為資料上鎖，即便在非同步模式下，SQLite 也能實現資料的原子性操作 (由於SQLite特性，原子性僅能在單程式範圍內實現)。
