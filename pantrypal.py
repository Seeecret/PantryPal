import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

try:
    from plyer import notification
except ImportError:
    notification = None

APP_NAME = "PantryPal"
DB_PATH = Path(__file__).with_name("pantrypal.db")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class DB:
    def __init__(self):
        self.c = sqlite3.connect(DB_PATH)
        self.c.row_factory = sqlite3.Row
        self.c.execute("""CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, quantity INTEGER NOT NULL DEFAULT 1,
            category TEXT NOT NULL DEFAULT 'Other', expiry TEXT NOT NULL,
            notes TEXT DEFAULT '', reminded INTEGER NOT NULL DEFAULT 0)""")
        self.c.commit()

    def all(self):
        return self.c.execute("SELECT * FROM foods ORDER BY expiry,name").fetchall()

    def add(self, name, qty, cat, expiry, notes):
        self.c.execute("INSERT INTO foods(name,quantity,category,expiry,notes) VALUES(?,?,?,?,?)",
                       (name, qty, cat, expiry, notes))
        self.c.commit()

    def update(self, fid, name, qty, cat, expiry, notes):
        self.c.execute("""UPDATE foods SET name=?,quantity=?,category=?,expiry=?,notes=?,reminded=0
                          WHERE id=?""", (name, qty, cat, expiry, notes, fid))
        self.c.commit()

    def delete(self, fid):
        self.c.execute("DELETE FROM foods WHERE id=?", (fid,))
        self.c.commit()

    def remind(self, fid):
        self.c.execute("UPDATE foods SET reminded=1 WHERE id=?", (fid,))
        self.c.commit()

    def close(self):
        self.c.close()


class PantryPal(ctk.CTk):
    BG="#0b0f14"; PANEL="#11161d"; CARD="#151b23"; HOVER="#1d2630"
    BORDER="#26303b"; TEXT="#f4f7fb"; MUTED="#8b97a7"
    BLUE="#5b8cff"; ORANGE="#f3a43b"; RED="#ff5d6c"; GREEN="#43c77a"

    def __init__(self):
        super().__init__()
        self.title(APP_NAME); self.geometry("1200x760"); self.minsize(1000,650)
        self.configure(fg_color=self.BG)
        self.db=DB(); self.filter="all"; self.search=tk.StringVar()
        self.category=tk.StringVar(value="All Categories")
        self.stats={}
        self.build_sidebar(); self.build_main(); self.refresh()
        self.search.trace_add("write", lambda *_: self.refresh())
        self.after(1000,self.check_reminders)
        self.protocol("WM_DELETE_WINDOW",self.close_app)

    def nav(self, parent, text, filt):
        b=ctk.CTkButton(parent,text=text,height=42,corner_radius=9,anchor="w",
                        fg_color="transparent",hover_color=self.HOVER,text_color=self.MUTED,
                        font=ctk.CTkFont(size=12),command=lambda:self.set_filter(filt))
        b.pack(fill="x",padx=12,pady=2)

    def build_sidebar(self):
        s=ctk.CTkFrame(self,width=225,corner_radius=0,fg_color=self.PANEL)
        s.pack(side="left",fill="y"); s.pack_propagate(False)
        ctk.CTkLabel(s,text="🥬",font=ctk.CTkFont(size=30)).pack(anchor="w",padx=22,pady=(27,0))
        ctk.CTkLabel(s,text="PantryPal",font=ctk.CTkFont(size=21,weight="bold"),
                     text_color=self.TEXT).pack(anchor="w",padx=22,pady=(3,0))
        ctk.CTkLabel(s,text="Food expiry tracker",font=ctk.CTkFont(size=10),
                     text_color=self.MUTED).pack(anchor="w",padx=23,pady=(0,30))
        ctk.CTkLabel(s,text="MENU",font=ctk.CTkFont(size=9,weight="bold"),
                     text_color="#596474").pack(anchor="w",padx=24,pady=(0,7))
        for t,f in [("⌂   Dashboard","all"),("▣   All Food","all"),
                    ("!   Expiring Soon","soon"),("✓   Fresh","fresh"),("×   Expired","expired")]:
            self.nav(s,t,f)
        ctk.CTkFrame(s,height=1,fg_color=self.BORDER).pack(fill="x",padx=22,pady=22)
        ctk.CTkButton(s,text="+  Add Food",height=42,corner_radius=10,fg_color=self.BLUE,
                      hover_color="#4c79e6",font=ctk.CTkFont(weight="bold"),
                      command=self.add_food).pack(fill="x",padx=20)
        ctk.CTkFrame(s,fg_color="transparent").pack(fill="both",expand=True)
        ctk.CTkLabel(s,text="LOCAL DATABASE",font=ctk.CTkFont(size=9,weight="bold"),
                     text_color="#596474").pack(anchor="w",padx=24)
        ctk.CTkLabel(s,text="Your data stays on this PC",font=ctk.CTkFont(size=10),
                     text_color=self.MUTED).pack(anchor="w",padx=24,pady=(2,20))

    def build_main(self):
        m=ctk.CTkFrame(self,fg_color=self.BG,corner_radius=0); m.pack(side="left",fill="both",expand=True)
        top=ctk.CTkFrame(m,fg_color="transparent"); top.pack(fill="x",padx=35,pady=(30,0))
        ctk.CTkLabel(top,text="Your pantry",font=ctk.CTkFont(size=28,weight="bold"),
                     text_color=self.TEXT).pack(anchor="w")
        ctk.CTkLabel(top,text=date.today().strftime("%A, %d %B %Y"),
                     font=ctk.CTkFont(size=12),text_color=self.MUTED).pack(anchor="w")
        ctk.CTkButton(top,text="+  Add Food",width=125,height=40,corner_radius=10,
                      fg_color=self.BLUE,hover_color="#4c79e6",
                      command=self.add_food).pack(side="right",pady=(0,8))

        sf=ctk.CTkFrame(m,fg_color="transparent"); sf.pack(fill="x",padx=35,pady=(28,22))
        for key,title,accent in [("total","TOTAL ITEMS",self.BLUE),("soon","EXPIRING SOON",self.ORANGE),
                                 ("expired","EXPIRED",self.RED),("fresh","FRESH",self.GREEN)]:
            card=ctk.CTkFrame(sf,fg_color=self.CARD,corner_radius=12,border_width=1,
                              border_color=self.BORDER,height=88)
            card.pack(side="left",fill="x",expand=True,padx=(0,10)); card.pack_propagate(False)
            ctk.CTkLabel(card,text=title,font=ctk.CTkFont(size=9,weight="bold"),
                         text_color=self.MUTED).pack(anchor="w",padx=18,pady=(13,0))
            lab=ctk.CTkLabel(card,text="0",font=ctk.CTkFont(size=23,weight="bold"),
                             text_color=self.TEXT); lab.pack(anchor="w",padx=18)
            self.stats[key]=lab

        h=ctk.CTkFrame(m,fg_color="transparent"); h.pack(fill="x",padx=35)
        self.title_lab=ctk.CTkLabel(h,text="All Food",font=ctk.CTkFont(size=18,weight="bold"),
                                    text_color=self.TEXT); self.title_lab.pack(side="left")
        self.searchbox=ctk.CTkEntry(h,width=210,height=36,corner_radius=9,
                                     placeholder_text="⌕  Search food...",textvariable=self.search,
                                     fg_color=self.CARD,border_color=self.BORDER)
        self.searchbox.pack(side="right",padx=(8,0))
        ctk.CTkComboBox(h,width=155,height=36,values=["All Categories","Dairy","Meat","Fruit & Vegetables",
                         "Bakery","Frozen","Tinned","Drinks","Other"],variable=self.category,
                        fg_color=self.CARD,border_color=self.BORDER,
                        command=lambda _:self.refresh()).pack(side="right")
        self.cards=ctk.CTkScrollableFrame(m,fg_color="transparent")
        self.cards.pack(fill="both",expand=True,padx=28,pady=(15,25))
        self.cards.grid_columnconfigure((0,1),weight=1)

    def status(self, expiry):
        days=(date.fromisoformat(expiry)-date.today()).days
        if days<0:return "Expired",days,"expired"
        if days==0:return "Expires today",days,"soon"
        if days==1:return "Expires tomorrow",days,"soon"
        if days<=3:return f"{days} days left",days,"soon"
        return f"{days} days left",days,"fresh"

    def set_filter(self,f):
        self.filter=f
        self.title_lab.configure(text={"all":"All Food","soon":"Expiring Soon","fresh":"Fresh Food","expired":"Expired Food"}[f])
        self.refresh()

    def refresh(self):
        for w in self.cards.winfo_children(): w.destroy()
        foods=self.db.all(); shown=[]; q=self.search.get().lower().strip(); cat=self.category.get()
        for food in foods:
            st,days,key=self.status(food["expiry"])
            if self.filter=="soon" and key!="soon":continue
            if self.filter=="fresh" and key!="fresh":continue
            if self.filter=="expired" and key!="expired":continue
            if q and q not in f'{food["name"]} {food["category"]} {food["notes"]}'.lower():continue
            if cat!="All Categories" and food["category"]!=cat:continue
            shown.append((food,st,key))
        for i,(food,st,key) in enumerate(shown):
            card=self.food_card(food,st,key); card.grid(row=i//2,column=i%2,sticky="ew",padx=7,pady=7)
        self.update_stats(foods)
        if not shown:
            e=ctk.CTkFrame(self.cards,fg_color=self.CARD,corner_radius=14,border_width=1,border_color=self.BORDER)
            e.grid(row=0,column=0,columnspan=2,sticky="ew",padx=7,pady=7)
            ctk.CTkLabel(e,text="🥬",font=ctk.CTkFont(size=35)).pack(pady=(35,4))
            ctk.CTkLabel(e,text="Nothing here yet",font=ctk.CTkFont(size=17,weight="bold"),
                         text_color=self.TEXT).pack()
            ctk.CTkLabel(e,text="Add some food to start tracking your pantry.",
                         text_color=self.MUTED).pack(pady=(4,30))

    def food_card(self,food,st,key):
        accent={"expired":self.RED,"soon":self.ORANGE,"fresh":self.GREEN}[key]
        emoji={"Dairy":"🥛","Meat":"🥩","Fruit & Vegetables":"🥦","Bakery":"🍞",
               "Frozen":"❄️","Tinned":"🥫","Drinks":"🥤","Other":"📦"}.get(food["category"],"📦")
        c=ctk.CTkFrame(self.cards,fg_color=self.CARD,corner_radius=14,border_width=1,
                       border_color=self.BORDER,height=158); c.pack_propagate(False)
        left=ctk.CTkFrame(c,width=4,fg_color=accent,corner_radius=2); left.pack(side="left",fill="y",padx=(0,14),pady=15)
        body=ctk.CTkFrame(c,fg_color="transparent"); body.pack(fill="both",expand=True,pady=15,padx=(0,14))
        top=ctk.CTkFrame(body,fg_color="transparent"); top.pack(fill="x")
        ctk.CTkLabel(top,text=emoji,font=ctk.CTkFont(size=25)).pack(side="left")
        nf=ctk.CTkFrame(top,fg_color="transparent"); nf.pack(side="left",padx=10)
        ctk.CTkLabel(nf,text=food["name"],font=ctk.CTkFont(size=14,weight="bold"),
                     text_color=self.TEXT).pack(anchor="w")
        ctk.CTkLabel(nf,text=f'{food["category"]}  •  Qty {food["quantity"]}',
                     font=ctk.CTkFont(size=10),text_color=self.MUTED).pack(anchor="w")
        ctk.CTkButton(top,text="•••",width=30,height=30,fg_color="transparent",
                      hover_color=self.HOVER,text_color=self.MUTED,
                      command=lambda f=food:self.actions(f)).pack(side="right")
        bot=ctk.CTkFrame(body,fg_color="transparent"); bot.pack(fill="x",pady=(20,0))
        ctk.CTkLabel(bot,text=st,font=ctk.CTkFont(size=12,weight="bold"),
                     text_color=accent).pack(side="left")
        ctk.CTkLabel(bot,text=datetime.strptime(food["expiry"],"%Y-%m-%d").strftime("%d %b %Y"),
                     font=ctk.CTkFont(size=10),text_color=self.MUTED).pack(side="right")
        if food["notes"]:
            ctk.CTkLabel(body,text=food["notes"],font=ctk.CTkFont(size=9),
                         text_color=self.MUTED).pack(anchor="w",pady=(7,0))
        return c

    def update_stats(self,foods):
        n={"total":len(foods),"soon":0,"expired":0,"fresh":0}
        for f in foods:
            _,days,k=self.status(f["expiry"])
            n["expired" if days<0 else "soon" if days<=3 else "fresh"]+=1
        for k,v in n.items():self.stats[k].configure(text=str(v))

    def actions(self,food):
        w=ctk.CTkToplevel(self); w.title(food["name"]); w.geometry("320x220"); w.resizable(False,False)
        w.configure(fg_color=self.BG); w.transient(self); w.grab_set()
        ctk.CTkLabel(w,text=food["name"],font=ctk.CTkFont(size=19,weight="bold")).pack(pady=(25,4))
        ctk.CTkLabel(w,text=f'{food["category"]} • Quantity {food["quantity"]}',text_color=self.MUTED).pack(pady=(0,18))
        ctk.CTkButton(w,text="Edit",command=lambda:(w.destroy(),self.food_window(food))).pack(fill="x",padx=25,pady=4)
        ctk.CTkButton(w,text="Delete",fg_color="#3a1d23",hover_color="#51232d",text_color="#ff8791",
                      command=lambda:self.delete(food,w)).pack(fill="x",padx=25,pady=4)

    def food_window(self,food=None):
        w=ctk.CTkToplevel(self); w.title("Edit Food" if food else "Add Food"); w.geometry("470x590")
        w.resizable(False,False); w.configure(fg_color=self.BG); w.transient(self); w.grab_set()
        ctk.CTkLabel(w,text="Edit Food" if food else "Add Food",font=ctk.CTkFont(size=22,weight="bold")).pack(anchor="w",padx=30,pady=(28,3))
        ctk.CTkLabel(w,text="Update your pantry item." if food else "Add an item to track its expiry.",
                     text_color=self.MUTED).pack(anchor="w",padx=30,pady=(0,20))
        f=ctk.CTkFrame(w,fg_color="transparent"); f.pack(fill="both",expand=True,padx=30)
        def field(label,default="",placeholder=""):
            ctk.CTkLabel(f,text=label,font=ctk.CTkFont(size=9,weight="bold"),text_color=self.MUTED).pack(anchor="w",pady=(0,5))
            e=ctk.CTkEntry(f,height=40,corner_radius=9,fg_color=self.CARD,border_color=self.BORDER,placeholder_text=placeholder)
            e.pack(fill="x",pady=(0,14))
            if default:e.insert(0,default)
            return e
        name=field("FOOD NAME",food["name"] if food else "","e.g. Milk")
        qty=field("QUANTITY",str(food["quantity"]) if food else "1")
        ctk.CTkLabel(f,text="CATEGORY",font=ctk.CTkFont(size=9,weight="bold"),text_color=self.MUTED).pack(anchor="w",pady=(0,5))
        cat=ctk.CTkComboBox(f,height=40,values=["Dairy","Meat","Fruit & Vegetables","Bakery","Frozen","Tinned","Drinks","Other"],
                            fg_color=self.CARD,border_color=self.BORDER); cat.pack(fill="x",pady=(0,14)); cat.set(food["category"] if food else "Other")
        default=datetime.strptime(food["expiry"],"%Y-%m-%d").strftime("%d/%m/%Y") if food else (date.today()+timedelta(days=7)).strftime("%d/%m/%Y")
        exp=field("EXPIRY DATE • DD/MM/YYYY",default)
        notes=field("NOTES",food["notes"] if food else "","Optional")
        def save():
            if not name.get().strip(): messagebox.showerror("Invalid item","Enter a food name.",parent=w); return
            try:q=int(qty.get()); assert q>0
            except: messagebox.showerror("Invalid quantity","Quantity must be 1 or more.",parent=w); return
            try:d=datetime.strptime(exp.get().strip(),"%d/%m/%Y").date()
            except ValueError: messagebox.showerror("Invalid date","Use DD/MM/YYYY.",parent=w); return
            if food:self.db.update(food["id"],name.get().strip(),q,cat.get(),d.isoformat(),notes.get().strip())
            else:self.db.add(name.get().strip(),q,cat.get(),d.isoformat(),notes.get().strip())
            w.destroy();self.refresh()
        ctk.CTkButton(w,text="Save Food",height=43,fg_color=self.BLUE,hover_color="#4c79e6",
                      command=save).pack(fill="x",padx=30,pady=(0,25))

    def add_food(self):self.food_window()

    def delete(self,food,w):
        if messagebox.askyesno("Delete food",f"Delete '{food['name']}'?",parent=w):
            self.db.delete(food["id"]);w.destroy();self.refresh()

    def check_reminders(self):
        for f in self.db.all():
            _,days,_=self.status(f["expiry"])
            if days in (3,1,0) and not f["reminded"]:
                msg=f'{f["name"]} expires today.' if days==0 else f'{f["name"]} expires tomorrow.' if days==1 else f'{f["name"]} expires in {days} days.'
                if notification:
                    try:notification.notify(title=APP_NAME,message=msg,app_name=APP_NAME,timeout=8)
                    except:pass
                self.db.remind(f["id"])
        self.after(3600000,self.check_reminders)

    def close_app(self):self.db.close();self.destroy()


if __name__=="__main__":
    PantryPal().mainloop()
