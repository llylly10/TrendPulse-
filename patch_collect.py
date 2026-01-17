import os

file_path = r'd:\demo\collect.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Patch fetch_reddit
old_reddit = '''    except Exception as e:
        print(f"❌ Reddit 抓取失败: {e}")
        return []'''
new_reddit = '''    except requests.exceptions.Timeout:
        print("❌ Reddit 请求超时，跳过。")
        return []
    except Exception as e:
        print(f"❌ Reddit 抓取失败: {e}")
        return []'''

# Patch fetch_youtube
old_youtube = '''    except Exception as e:
        print(f"❌ YouTube 搜索失败: {e}")
        return []'''
new_youtube = '''    except requests.exceptions.Timeout:
        print("❌ YouTube 请求超时，跳过。")
        return []
    except Exception as e:
        print(f"❌ YouTube 搜索失败: {e}")
        return []'''

# Patch fetch_twitter
old_twitter = '''        except Exception as e:
            print(f"   ❌ 访问 {instance} 出错: {e}")
            continue'''
new_twitter = '''        except requests.exceptions.Timeout:
            print(f"   ❌ 访问 {instance} 超时，跳过。")
            continue
        except Exception as e:
            print(f"   ❌ 访问 {instance} 出错: {e}")
            continue'''

content = content.replace(old_reddit, new_reddit)
content = content.replace(old_youtube, new_youtube)
content = content.replace(old_twitter, new_twitter)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully patched collect.py")
