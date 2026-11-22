#include <algorithm>
#include <cassert>
#include <chrono>
#include <cctype>
#include <cmath>
#include <functional>
#include <iostream>
#include <numeric>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

struct Complaint { std::string id, category, locality, place, text; };
class ComplaintIndex {
    std::unordered_map<std::string, size_t> positions;
public:
    bool insert(const std::string& id, size_t position) { return positions.emplace(id, position).second; }
    bool find(const std::string& id, size_t& position) const {
        auto item=positions.find(id);
        if(item==positions.end()) return false;
        position=item->second; return true;
    }
    bool update(const std::string& id, size_t position) {
        auto item=positions.find(id); if(item==positions.end()) return false;
        item->second=position; return true;
    }
    bool remove(const std::string& id) { return positions.erase(id)>0; }
};
std::string clean(std::string s) {
    std::string out; bool space = true;
    for (unsigned char ch : s) {
        if (std::isalnum(ch)) { out += static_cast<char>(std::tolower(ch)); space = false; }
        else if (!space) { out += ' '; space = true; }
    }
    if (!out.empty() && out.back() == ' ') out.pop_back();
    return out;
}
int distance(const std::string& a, const std::string& b) {
    // Keep the row width equal to the shorter string for O(min(m,n)) space.
    if (b.size() > a.size()) return distance(b, a);
    std::vector<int> prev(b.size()+1), cur(b.size()+1);
    for (size_t j=0;j<=b.size();++j) prev[j]=static_cast<int>(j);
    for (size_t i=1;i<=a.size();++i) {
        cur[0]=static_cast<int>(i);
        for (size_t j=1;j<=b.size();++j) cur[j]=std::min({prev[j]+1,cur[j-1]+1,prev[j-1]+(a[i-1]==b[j-1]?0:1)});
        prev.swap(cur);
    }
    return prev[b.size()];
}
double similarity(std::string a, std::string b) {
    a=clean(a); b=clean(b); size_t n=std::max(a.size(),b.size());
    if (n==0) return 1.0;
    return 1.0-static_cast<double>(distance(a,b))/n;
}
struct Issue { std::string id; double score; };
class MaxHeap {
    std::vector<Issue> data;
    bool higher(const Issue& a,const Issue& b) { return a.score==b.score ? a.id<b.id : a.score>b.score; }
public:
    void push(Issue x) { data.push_back(x); size_t i=data.size()-1; while(i>0){size_t p=(i-1)/2;if(!higher(data[i],data[p]))break;std::swap(data[i],data[p]);i=p;} }
    Issue pop() { Issue top=data.front(); data[0]=data.back(); data.pop_back(); size_t i=0; while(i<data.size()){size_t best=i,l=2*i+1,r=l+1;if(l<data.size()&&higher(data[l],data[best]))best=l;if(r<data.size()&&higher(data[r],data[best]))best=r;if(best==i)break;std::swap(data[i],data[best]);i=best;} return top; }
    bool empty() const { return data.empty(); }
};
void merge_sort(std::vector<int>& values, std::vector<int>& scratch, size_t first, size_t last) {
    if (last-first < 2) return;
    size_t middle=first+(last-first)/2;
    merge_sort(values,scratch,first,middle);
    merge_sort(values,scratch,middle,last);
    size_t left=first,right=middle,out=first;
    while(left<middle&&right<last) scratch[out++]=(values[left]<=values[right])?values[left++]:values[right++];
    while(left<middle) scratch[out++]=values[left++];
    while(right<last) scratch[out++]=values[right++];
    for(size_t i=first;i<last;++i) values[i]=scratch[i];
}
long long elapsed_ns(const std::function<void()>& operation) {
    auto start=std::chrono::high_resolution_clock::now(); operation();
    return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::high_resolution_clock::now()-start).count();
}
void run_benchmark() {
    const std::vector<int> sizes={100,500,1000,5000};
    std::cout<<"size\tlinear_ns\thash_ns\tmerge_sort_ns\theap_ns\tduplicate_scan_ns\n";
    for(int n:sizes) {
        std::vector<int> values(n); std::iota(values.begin(),values.end(),0);
        std::unordered_map<int,int> lookup; lookup.reserve(n*2);
        for(int i=0;i<n;++i) lookup.emplace(i,i);
        volatile int sink=0;
        long long linear=elapsed_ns([&]{for(int repeat=0;repeat<100;++repeat)for(int i=0;i<n;++i)if(values[i]==n-1){sink+=values[i];break;}});
        long long hashed=elapsed_ns([&]{for(int repeat=0;repeat<100;++repeat){auto found=lookup.find(n-1);if(found!=lookup.end())sink+=found->second;}});
        std::vector<int> unsorted=values; std::reverse(unsorted.begin(),unsorted.end());
        std::vector<int> scratch(n);
        long long sorting=elapsed_ns([&]{for(int repeat=0;repeat<3;++repeat){std::reverse(unsorted.begin(),unsorted.end());merge_sort(unsorted,scratch,0,unsorted.size());}})/3;
        long long heap_time=elapsed_ns([&]{for(int repeat=0;repeat<3;++repeat){MaxHeap heap;for(int i=0;i<n;++i)heap.push({std::to_string(i),static_cast<double>((i*37)%101)});while(!heap.empty())sink+=static_cast<int>(heap.pop().score);}})/3;
        std::vector<Complaint> complaints; complaints.reserve(n);
        for(int i=0;i<n;++i) complaints.push_back({std::to_string(i),"category"+std::to_string(i%7),"locality"+std::to_string(i%10),"landmark"+std::to_string(i%41),"simulated civic maintenance concern number"+std::to_string(i%73)});
        long long duplicate=elapsed_ns([&]{for(int repeat=0;repeat<3;++repeat){size_t suggestions=0;for(int i=0;i<n;++i)for(int j=i+1;j<n;++j){if(complaints[i].category!=complaints[j].category||complaints[i].locality!=complaints[j].locality)continue;double text=similarity(complaints[i].text,complaints[j].text);double place=similarity(complaints[i].place,complaints[j].place);if(.65*text+.35*place>=.35)++suggestions;}sink+=static_cast<int>(suggestions);}})/3;
        std::cout<<n<<'\t'<<linear<<'\t'<<hashed<<'\t'<<sorting<<'\t'<<heap_time<<'\t'<<duplicate<<'\n';
        if(sink==-1)std::cerr<<"";
    }
}
int main() {
    std::string action; if(!std::getline(std::cin,action)){std::cerr<<"missing action\n";return 2;}
    if(action=="score") {
        int severity, affected, age; if(!(std::cin>>severity>>affected>>age)||severity<1||severity>5||affected<0||age<0){std::cerr<<"invalid score input\n";return 2;}
        double s=(severity-1)*2.5, a=std::min(10.0,affected/10.0), w=std::min(10.0,age/7.0);
        std::cout<<std::fixed<<s*0.50+a*0.30+w*0.20<<"\n"; return 0;
    }
    if(action=="duplicates") {
        std::vector<Complaint> rows; std::string line;
        while(std::getline(std::cin,line)) { std::stringstream ss(line); Complaint c; std::getline(ss,c.id,'\t'); std::getline(ss,c.category,'\t'); std::getline(ss,c.locality,'\t'); std::getline(ss,c.place,'\t'); std::getline(ss,c.text); if(!c.id.empty())rows.push_back(c); }
        ComplaintIndex index;
        for(size_t i=0;i<rows.size();++i) index.insert(rows[i].id,i);
        std::cout<<"a\tb\tdescription_similarity\tlocation_similarity\toverall_score\n";
        for(size_t i=0;i<rows.size();++i) for(size_t j=i+1;j<rows.size();++j) {
            const auto& a=rows[i];const auto& b=rows[j];
            size_t position=0;
            if(!index.find(a.id,position)||position!=i) continue;
            if(clean(a.category)!=clean(b.category)||clean(a.locality)!=clean(b.locality))continue;
            double text=similarity(a.text,b.text), place=similarity(a.place,b.place);
            double total=0.65*text+0.35*place;
            if(total>=0.35) std::cout<<a.id<<'\t'<<b.id<<'\t'<<text<<'\t'<<place<<'\t'<<total<<'\n';
        }
        return 0;
    }
    if(action=="rank") {
        MaxHeap heap;std::string id;double score;
        while(std::cin>>id>>score)heap.push({id,score});
        while(!heap.empty()){auto x=heap.pop();std::cout<<x.id<<'\t'<<x.score<<'\n';}return 0;
    }
    if(action=="benchmark") { run_benchmark(); return 0; }
    if(action=="selftest") {
        ComplaintIndex index; size_t position=99;
        if(!index.insert("CR1",4)||index.insert("CR1",8)||!index.find("CR1",position)||position!=4||index.find("missing",position)||!index.update("CR1",7)||!index.find("CR1",position)||position!=7||!index.remove("CR1")||index.remove("CR1")){std::cerr<<"hash index check failed\n";return 1;}
        if(distance("kitten","sitting")!=3||distance("","abc")!=3||similarity("!!!"," ")!=1.0||similarity("","x")!=0.0){std::cerr<<"similarity check failed\n";return 1;}
        std::vector<int> values={4,1,3,1,0};std::vector<int> scratch(values.size());merge_sort(values,scratch,0,values.size());
        if(!std::is_sorted(values.begin(),values.end())){std::cerr<<"merge sort check failed\n";return 1;}
        MaxHeap heap;heap.push({"IS2",8});heap.push({"IS1",8});heap.push({"IS3",4});
        if(heap.pop().id!="IS1"||heap.pop().id!="IS2"||heap.pop().id!="IS3"||!heap.empty()){std::cerr<<"heap check failed\n";return 1;}
        std::cout<<"C++ algorithm self-tests passed\n";return 0;
    }
    std::cerr<<"unknown action\n";return 2;
}
